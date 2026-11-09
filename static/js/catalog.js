// Sin JavaScript los filtros quedan abiertos y siguen funcionando por GET.
const filters = document.querySelector('.filter-panel');
if (filters) {
    const desktop = window.matchMedia('(min-width: 1000px)');
    const adjustFilters = () => {
        if (desktop.matches || filters.dataset.hasErrors === 'true') {
            filters.open = true;
        } else if (!filters.contains(document.activeElement)) {
            filters.open = false;
        }
    };
    adjustFilters();
    desktop.addEventListener('change', adjustFilters);
}
