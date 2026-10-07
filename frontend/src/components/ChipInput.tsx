import { useState, type KeyboardEvent } from 'react'

interface Props {
  value: string[]
  onChange: (value: string[]) => void
  placeholder?: string
}

/** List editor: type and press Enter or comma to add, click a chip to remove it. */
export default function ChipInput({ value, onChange, placeholder }: Props) {
  const [draft, setDraft] = useState('')

  function commit() {
    const items = draft.split(',').map((item) => item.trim()).filter((item) => item && !value.includes(item))
    if (items.length) onChange([...value, ...items])
    setDraft('')
  }

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Enter' || event.key === ',') {
      event.preventDefault()
      commit()
    } else if (event.key === 'Backspace' && !draft && value.length) {
      onChange(value.slice(0, -1))
    }
  }

  return (
    <div className="chip-input">
      {value.map((item) => (
        <button type="button" key={item} className="chip removable" onClick={() => onChange(value.filter((v) => v !== item))} title="Quitar">
          {item} <span aria-hidden>×</span>
        </button>
      ))}
      <input value={draft} onChange={(e) => setDraft(e.target.value)} onKeyDown={onKeyDown} onBlur={commit} placeholder={value.length ? '' : placeholder} />
    </div>
  )
}
