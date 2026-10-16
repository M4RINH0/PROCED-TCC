/* Ícones autorais do protótipo, traço único de 1,6 */
const TRACOS = {
  pan: (
    <>
      <path d="M3.5 19.5h17" />
      <path d="M5 16.5c3-1 4.5-5.5 7.5-6.5S17.5 9 19 5" />
      <path d="M15 5v15" strokeDasharray="1.6 2.4" />
    </>
  ),
  dom: (
    <>
      <path d="M4 11 12 4.5 20 11" />
      <path d="M6 10v9.5h12V10" />
      <path d="M10.5 19.5v-5h3v5" />
    </>
  ),
  eta: (
    <>
      <path d="M9.5 4.5h5M7.5 8.5h9M5.5 12.5h13M3.5 16.5h17" />
      <path d="M12 19.5v-15" opacity=".45" />
    </>
  ),
  sim: (
    <>
      <path d="M4 7h9M17 7h3M4 12h3M11 12h9M4 17h11M19 17h1" />
      <circle cx="15" cy="7" r="2" />
      <circle cx="9" cy="12" r="2" />
      <circle cx="17" cy="17" r="2" />
    </>
  ),
  info: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 11v5M12 7.8v.2" />
    </>
  ),
  alert: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.8v5M12 16v.2" />
    </>
  ),
  db: (
    <>
      <ellipse cx="12" cy="6" rx="7.5" ry="2.8" />
      <path d="M4.5 6v12c0 1.5 3.4 2.8 7.5 2.8s7.5-1.3 7.5-2.8V6" />
      <path d="M4.5 12c0 1.5 3.4 2.8 7.5 2.8s7.5-1.3 7.5-2.8" />
    </>
  ),
  api: <path d="M8.5 7.5 4 12l4.5 4.5M15.5 7.5 20 12l-4.5 4.5M13.5 5l-3 14" />,
  down: <path d="M12 4v11M7.5 10.5 12 15l4.5-4.5M5 19.5h14" />,
  sun: (
    <>
      <circle cx="12" cy="12" r="3.8" />
      <path d="M12 2.8v2M12 19.2v2M2.8 12h2M19.2 12h2M5.5 5.5l1.4 1.4M17.1 17.1l1.4 1.4M18.5 5.5l-1.4 1.4M6.9 17.1l-1.4 1.4" />
    </>
  ),
  moon: <path d="M19.5 14.2A7.8 7.8 0 1 1 9.8 4.5a6.2 6.2 0 0 0 9.7 9.7z" />,
  x: <path d="M6.5 6.5l11 11M17.5 6.5l-11 11" />,
  chev: <path d="M7 10l5 5 5-5" />,
  target: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <circle cx="12" cy="12" r="4" />
      <circle cx="12" cy="12" r=".8" fill="currentColor" />
    </>
  ),
  refresh: (
    <>
      <path d="M19.5 11.5a7.5 7.5 0 1 1-2.4-5.2" />
      <path d="M19.5 4.5v4h-4" />
    </>
  ),
  flask: (
    <>
      <path d="M9.5 3.5h5M10.5 3.5v5.2L5.2 17.6A2 2 0 0 0 6.9 20.5h10.2a2 2 0 0 0 1.7-2.9L13.5 8.7V3.5" />
      <path d="M7.6 14.5h8.8" />
    </>
  ),
  copy: (
    <>
      <rect x="8.5" y="8.5" width="11" height="11" rx="2.2" />
      <path d="M15.5 8.5V6.2A1.7 1.7 0 0 0 13.8 4.5H6.2a1.7 1.7 0 0 0-1.7 1.7v7.6a1.7 1.7 0 0 0 1.7 1.7h2.3" />
    </>
  ),
}

export const CAMINHO_CASA = 'M10 1.6 19 9.2h-2.2V18.6H3.2V9.2H1Z M8.3 18.6v-5.2h3.4v5.2Z'

export default function Icone({ nome }) {
  if (nome === 'logo') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <rect x="2" y="2" width="20" height="20" rx="6" fill="#F2B01E" />
        <path d="M13 5.5 7.5 13.2h4.1l-1 5.3 5.8-7.9h-4.2z" fill="#1D1603" />
      </svg>
    )
  }
  if (nome === 'play') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M8 5.5v13l10.5-6.5z" fill="currentColor" />
      </svg>
    )
  }
  if (nome === 'pause') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <rect x="7" y="5.5" width="3.6" height="13" rx="1" fill="currentColor" />
        <rect x="13.4" y="5.5" width="3.6" height="13" rx="1" fill="currentColor" />
      </svg>
    )
  }
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      data-icone={nome}
    >
      {TRACOS[nome]}
    </svg>
  )
}
