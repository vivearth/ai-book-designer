import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variant = 'primary' | 'secondary' | 'ghost' | 'icon'
type Size = 'sm' | 'md' | 'lg'

export function Button({ variant = 'secondary', size = 'md', className = '', children, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: Size; children: ReactNode }) {
  return <button {...props} className={`ui-btn ui-btn--${variant} ui-btn--${size} ${className}`.trim()}>{children}</button>
}
