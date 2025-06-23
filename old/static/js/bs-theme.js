(() => {
    'use strict'
  
    const getStoredTheme = () => localStorage.getItem('theme')
    const setStoredTheme = theme => localStorage.setItem('theme', theme)
  
    const getPreferredTheme = () => {
        const storedTheme = getStoredTheme()
        if (storedTheme) {
          return storedTheme
        }
        // If no stored theme, get system preference and store it
        const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
        setStoredTheme(systemTheme)  // Store the system preference
        return systemTheme
      }
  
    const setTheme = theme => {
      document.documentElement.setAttribute('data-bs-theme', theme)
      // Update the toggle button icon
      const themeToggle = document.querySelector('#darkModeToggle')
      if (themeToggle) {
        themeToggle.innerHTML = theme === 'dark' ? '☀️' : '🌙'
        themeToggle.setAttribute('data-bs-theme-value', theme === 'dark' ? 'light' : 'dark')
        document.documentElement.classList.toggle('dark', theme === 'dark')
      }
    }
  
    // Initialize theme
    setTheme(getPreferredTheme())
  
    // Handle theme toggle click
    document.addEventListener('DOMContentLoaded', () => {
      const themeToggle = document.querySelector('#darkModeToggle')
      if (themeToggle) {
        themeToggle.addEventListener('click', () => {
          const currentTheme = getStoredTheme() || getPreferredTheme()
          const newTheme = currentTheme === 'dark' ? 'light' : 'dark'
          setStoredTheme(newTheme)
          setTheme(newTheme)
        })
      }
    })
  
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      const storedTheme = getStoredTheme()
      if (!storedTheme) {
        setTheme(getPreferredTheme())
      }
    })
})()