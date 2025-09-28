import './globals.css'

export const metadata = {
  title: 'IST Lunch - Sundbybergs bästa lunchguide',
  description: 'Hitta dagens bästa lunch nära IST kontoret i Sundbyberg',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="sv">
      <body className="font-sans antialiased">{children}</body>
    </html>
  )
}
