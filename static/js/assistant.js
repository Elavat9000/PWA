(() => {
    const panel = document.getElementById('assistant-panel');
    if (!panel) return;
    const launcher = document.getElementById('assistant-launcher');
    const form = document.getElementById('assistant-form');
    const input = document.getElementById('assistant-message');
    const conversation = document.getElementById('assistant-conversation');
    const progress = document.getElementById('assistant-progress');
    const send = form.querySelector('button[type="submit"]');

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
        conversation.scrollTop = conversation.scrollHeight;
    }

    function appendVehicles(vehicles) {
        for (const vehicle of vehicles) {
            const article = document.createElement('article');
            article.className = 'assistant-vehicle';
            const link = document.createElement('a');
            link.href = vehicle.url;
            link.textContent = vehicle.name;
            const details = document.createElement('p');
            details.textContent = `$${vehicle.daily_price} MXN / día · ${vehicle.passengers} pasajeros · ${vehicle.transmission}`;
            const availability = document.createElement('small');
            availability.textContent = vehicle.available ? 'Disponible en catálogo' : 'No disponible';
            article.append(link, details, availability);
            conversation.append(article);
        }
        conversation.scrollTop = conversation.scrollHeight;
    }

    form.addEventListener('submit', async event => {
        event.preventDefault();
        const message = input.value.trim();
        if (!form.reportValidity() || send.disabled || message.length < 2) return;
        appendMessage(message, true);
        input.value = '';
        send.disabled = true;
        progress.textContent = 'Consultando…';
        form.setAttribute('aria-busy', 'true');
        try {
            const response = await fetch(panel.dataset.endpoint, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': form.querySelector('[name="csrfmiddlewaretoken"]').value,
                },
                body: JSON.stringify({ message }),
            });
            if (!response.ok) throw new Error(String(response.status));
            const data = await response.json();
            appendMessage(data.reply);
            appendVehicles(data.vehicles);
        } catch (error) {
            appendMessage(error.message === '403'
                ? 'Recarga la página para renovar la sesión segura e intenta nuevamente.'
                : 'No pude consultar en este momento. Intenta nuevamente.');
            input.value = message;
        } finally {
            progress.textContent = '';
            form.removeAttribute('aria-busy');
            send.disabled = false;
            if (panel.open) input.focus();
        }
    });
})();
