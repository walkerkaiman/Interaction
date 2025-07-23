import React from 'react';
import ReactDOM from 'react-dom/client';
import { CacheProvider } from '@emotion/react';
import createCache from '@emotion/cache';
import App from './App';

const cache = createCache({
  key: 'css',
  prepend: true,
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <CacheProvider value={cache}>
      <App />
    </CacheProvider>
  </React.StrictMode>
);
