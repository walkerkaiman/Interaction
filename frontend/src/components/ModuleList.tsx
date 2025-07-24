import React, { useEffect, useState } from 'react';

const ModuleList: React.FC = () => {
  const [modules, setModules] = useState<{ name: string }[]>([]);
  useEffect(() => {
    fetch('/modules').then(res => res.json()).then(setModules);
  }, []);
  return (
    <ul>
      {modules.map(m => <li key={m.name}>{m.name}</li>)}
    </ul>
  );
};

export default ModuleList; 