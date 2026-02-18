/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/clerk/web/templates/**/*.html",
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
                logo: ['Bodoni Moda SC', 'serif'],
            },
            colors: {
                primary: {
                    DEFAULT: '#130DDD',
                    foreground: '#ffffff',
                },
                foreground: '#111418',
                muted: {
                    DEFAULT: '#f4f6f9',
                    foreground: '#6b7280',
                },
                border: 'rgba(0,0,0,0.1)',
                destructive: {
                    DEFAULT: '#ef4444',
                    foreground: '#ffffff',
                },
            },
            borderRadius: {
                sm: '0.375rem',
                md: '0.625rem',
                lg: '0.75rem',
                xl: '1rem',
                '2xl': '1.25rem',
            },
        },
    },
    plugins: [],
}
