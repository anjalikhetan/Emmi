/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
  	extend: {
  		colors: {
  			primary: 'hsl(var(--primary))',
  			secondary: 'hsl(var(--secondary))',
  			accent: 'hsl(var(--accent))',
  			background: 'hsl(var(--background))',
  			popover: 'hsl(var(--popover))',
  			foreground: 'hsl(var(--text))'
  		},
  		fontFamily: {
  			sans: [
  				'var(--font-open-sans)'
  			],
  			cormorant: [
  				'var(--font-cormorant)'
  			]
  		},
  		borderRadius: {
  			lg: 'calc(var(--border-radius) + 4px)',
  			md: 'calc(var(--border-radius) + 2px)',
  			default: 'var(--border-radius)',
  			sm: 'calc(var(--border-radius) - 2px)'
  		},
  		keyframes: {
  			'accordion-down': {
  				from: {
  					height: '0'
  				},
  				to: {
  					height: 'var(--radix-accordion-content-height)'
  				}
  			},
  			'accordion-up': {
  				from: {
  					height: 'var(--radix-accordion-content-height)'
  				},
  				to: {
  					height: '0'
  				}
  			}
  		},
  		animation: {
  			'accordion-down': 'accordion-down 0.2s ease-out',
  			'accordion-up': 'accordion-up 0.2s ease-out'
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
};
