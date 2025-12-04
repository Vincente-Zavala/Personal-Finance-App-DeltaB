function togglePeriodSections(mode) {
    const monthSection = document.getElementById('monthyearsection');
    const customSection = document.getElementById('customsection');
    
    if (mode === 'custom') {
        monthSection.classList.add('d-none');
        customSection.classList.remove('d-none');
    } else {
        monthSection.classList.remove('d-none');
        customSection.classList.add('d-none');
    }
}
