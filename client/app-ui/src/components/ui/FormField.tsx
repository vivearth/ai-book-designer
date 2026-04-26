import type { InputHTMLAttributes, TextareaHTMLAttributes } from 'react'

export function TextField({ label, hint, ...props }: InputHTMLAttributes<HTMLInputElement> & { label: string; hint?: string }) {
  return <label className="ui-field"><span>{label}</span><input {...props} />{hint ? <small>{hint}</small> : null}</label>
}

export function TextAreaField({ label, hint, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement> & { label: string; hint?: string }) {
  return <label className="ui-field"><span>{label}</span><textarea {...props} />{hint ? <small>{hint}</small> : null}</label>
}
