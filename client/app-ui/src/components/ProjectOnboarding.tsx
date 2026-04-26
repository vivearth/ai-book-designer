import { useState } from 'react'
import { api } from '../api'
import type { Project } from '../types'

export function ProjectOnboarding({ onCreated }: { onCreated: (project: Project) => void }) {
  const [name, setName] = useState('')
  const [contentDirection, setContentDirection] = useState('Marketing')
  const [audience, setAudience] = useState('CMOs')
  const [objective, setObjective] = useState('Convert curated materials into a polished book')

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    const project = await api.createProject({ name, content_direction: contentDirection, audience, objective, status: 'draft' })
    onCreated(project)
  }

  return (
    <form className="panel" onSubmit={submit}>
      <h2>Start a professional book project</h2>
      <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Project name" required />
      <select value={contentDirection} onChange={(e) => setContentDirection(e.target.value)}>
        <option>Marketing</option><option>Finance</option><option>Thought Leadership</option><option>Case-study collection</option>
      </select>
      <input value={audience} onChange={(e) => setAudience(e.target.value)} placeholder="Audience" />
      <textarea value={objective} onChange={(e) => setObjective(e.target.value)} placeholder="Objective" rows={3} />
      <button type="submit">Create project</button>
    </form>
  )
}
