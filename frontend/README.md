# React Frontend

Modern, high-performance React dashboard for the Quantum-Resistant Chaffing System.

## Features

- ⚡ **Vite**: Lightning-fast HMR and build times
- 🎨 **Ant Design**: Professional UI components
- 📊 **Recharts**: Beautiful, responsive charts
- 🔄 **Real-time Updates**: Live traffic visualization
- 🌙 **Dark Mode**: Modern dark theme
- 📱 **Responsive**: Works on all devices

## Setup

### Install Dependencies

```bash
cd frontend
npm install
```

### Run Development Server

```bash
npm run dev
```

Visit: http://localhost:3000

### Build for Production

```bash
npm run build
```

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/          # Page components
│   │   └── Dashboard.jsx
│   ├── services/       # API client
│   ├── utils/          # Utilities
│   ├── App.jsx         # Main app component
│   ├── main.jsx        # Entry point
│   └── index.css       # Global styles
├── public/             # Static assets
├── index.html          # HTML template
├── package.json        # Dependencies
└── vite.config.js      # Vite configuration
```

## Dashboard Features

- **Real-time Statistics**: Total packets, real/dummy ratio, throughput
- **Traffic Charts**: Area chart for packet flow, bar chart for size distribution
- **Live Packet Log**: Table showing recent packets with type, size, IAT
- **Engine Control**: Start/stop obfuscation engine
- **Overhead Monitoring**: Visual progress bar for traffic overhead

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000`.

API proxy is configured in `vite.config.js`:
```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

## Performance

- **Vite**: ~10x faster than Create React App
- **Code Splitting**: Automatic route-based splitting
- **Tree Shaking**: Removes unused code
- **Lazy Loading**: Components loaded on demand

## Technologies

- React 18
- Vite 5
- Ant Design 5
- Recharts 2
- React Router 6
- Axios

## Development

The dashboard updates in real-time when the engine is running. It simulates packet generation with:
- Random packet types (Real/Dummy)
- Variable packet sizes (100-1500 bytes)
- Inter-arrival times (0-100ms)
- Automatic statistics calculation

## Next Steps

- [ ] Connect to actual FastAPI backend
- [ ] Implement WebSocket for real-time updates
- [ ] Add authentication flow
- [ ] Create additional pages (Sessions, Crypto, Models)
- [ ] Add user settings and preferences
