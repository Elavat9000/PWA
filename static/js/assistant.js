(() => {
    const panel = document.getElementById('assistant-panel');
    if (!panel) return;
    const launcher = document.getElementById('assistant-launcher');
    const form = document.getElementById('assistant-form');
    const input = document.getElementById('assistant-message');
    const conversation = document.getElementById('assistant-conversation');
    const progress = document.getElementById('assistant-progress');
    const send = form.querySelector('button[type="submit"]');
    const reset = document.getElementById('assistant-reset');

    launcher.addEventListener('click', () => {
        panel.showModal();
        input.focus();
    });
    panel.querySelector('.assistant-close').addEventListener('click', () => panel.close());
    panel.addEventListener('close', () => launcher.focus());
    input.addEventListener('keydown', event => {
        if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
            event.preventDefault();
            form.requestSubmit();
        }
    });

    function appendMessage(text, fromUser = false) {
        const message = document.createElement('p');
        message.className = fromUser ? 'assistant-message from-user' : 'assistant-message';
        message.textContent = text;
        conversation.append(message);
        // El navegador tampoco conserva un historial ilimitado.
        while (conversation.children.length > 60) conversation.firstElementChild.remove();
        conversation.scrollTop = conversation.scrollHeight;
        return message;
    }

    function appendVehicles(vehicles) {
        for (const vehicle of vehicles) {
            const article = document.createElement('article');
            article.className = 'assistant-vehicle';
            const heading = document.createElement('h3');
            heading.textContent = vehicle.name;
            const price = document.createElement('strong');
            price.className = 'assistant-vehicle-price';
            price.textContent = `$${vehicle.daily_price} MXN / día`;
            const details = document.createElement('p');
            details.textContent = [vehicle.category, `${vehicle.passengers} pasajeros`, vehicle.transmission].filter(Boolean).join(' · ');
            const availability = document.createElement('small');
            availability.textContent = vehicle.availability_checked ? 'Disponible en las fechas consultadas · sujeto a nueva comprobación' : (vehicle.available ? 'Disponible en catálogo · fechas sin comprobar' : 'No disponible');
            const link = document.createElement('a');
            if (/^\/vehiculos\/\d+\/$/.test(vehicle.url)) link.href = vehicle.url;
            link.textContent = 'Ver vehículo';
            article.append(heading, price, details, availability, link);
            conversation.append(article);
        }
        conversation.scrollTop = conversation.scrollHeight;
    }

    function appendSuggestions(suggestions = []) {
        const group = document.createElement('div');
        group.className = 'assistant-suggestions';
        group.setAttribute('aria-label', 'Continuar la conversación');
        for (const text of suggestions.slice(0, 3)) {
            const button = document.createElement('button');
            button.type = 'button';
            button.textContent = text;
            button.addEventListener('click', () => submitQuestion(text));
            group.append(button);
        }
        conversation.append(group);
        conversation.scrollTop = conversation.scrollHeight;
    }

    async function request(payload) {
        send.disabled = true;
        reset.disabled = true;
        input.readOnly = true;
        progress.textContent = 'Consultando…';
        form.setAttribute('aria-busy', 'true');
        conversation.querySelectorAll('.assistant-suggestions').forEach(group => group.remove());
        try {
            const response = await fetch(panel.dataset.endpoint, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': form.querySelector('[name="csrfmiddlewaretoken"]').value,
                },
                body: JSON.stringify(payload),
            });
            if (!response.ok) throw new Error(String(response.status));
            const data = await response.json();
            if (payload.action === 'reset') {
                conversation.replaceChildren();
                input.value = '';
            }
            const reply = appendMessage(data.reply);
            appendVehicles(data.vehicles);
            appendSuggestions(data.suggestions);
            conversation.scrollTop = reply.offsetTop - conversation.offsetTop;
        } catch (error) {
            appendMessage(error.message === '403'
                ? 'Recarga la página para renovar la sesión segura e intenta nuevamente.'
                : 'No pude consultar en este momento. Intenta nuevamente.');
            if (payload.message) input.value = payload.message;
        } finally {
            progress.textContent = '';
            form.removeAttribute('aria-busy');
            send.disabled = false;
            reset.disabled = false;
            input.readOnly = false;
            if (panel.open) input.focus();
        }
    }

    function submitQuestion(message) {
        if (send.disabled || message.length < 2) return;
        appendMessage(message, true);
        input.value = '';
        request({ message });
    }

    reset.addEventListener('click', () => {
        if (!send.disabled) request({ action: 'reset' });
    });
    form.addEventListener('submit', event => {
        event.preventDefault();
        if (form.reportValidity()) submitQuestion(input.value.trim());
    });
})();
