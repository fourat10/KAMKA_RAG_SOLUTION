# Kamka Frontend

A Next.js + TypeScript + Tailwind CSS frontend for the Kamka Document Assistant API.

## Features

- **File Upload**: Upload PDF and TXT files (up to 20MB)
- **Document Management**: View and delete uploaded documents
- **Chat Interface**: Query documents with AI-powered answers
- **Citations**: View sources and excerpts from your documents
- **User Sessions**: Unique user ID for document ownership

## Getting Started

### Prerequisites

- Node.js 18+
- Backend running on `http://localhost:8000`

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/              # Next.js App Router
│   ├── layout.tsx    # Root layout
│   └── page.tsx      # Main page
├── components/       # Reusable React components
├── lib/             # Utility functions and stores
└── public/          # Static assets
```
