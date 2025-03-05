// script.ts

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // Get references to the settings button and the settings window
    const openSettingsButton = document.getElementById('open-settings') as HTMLButtonElement;
    const settingsWindow = document.getElementById('settings-window') as HTMLDivElement;

    // Function to open the settings window
    const openSettings = () => {
        settingsWindow.style.display = 'block';
    };

    // Function to close the settings window
    const closeSettings = () => {
        settingsWindow.style.display = 'none';
    };

    // Add event listener to the settings button to open the settings window
    openSettingsButton.addEventListener('click', openSettings);

    // Optional: Add event listener to close the settings window when clicking outside of it
    document.addEventListener('click', (event) => {
        if (settingsWindow.style.display === 'block' && !settingsWindow.contains(event.target as Node) && event.target !== openSettingsButton) {
            closeSettings();
        }
    });
});