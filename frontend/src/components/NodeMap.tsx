import React, { useEffect, useState } from 'react';

type Module = { name: string };
type Interaction = { input: { module: string }, output: { module: string } };

const NodeMap: React.FC = () => {
  const [modules, setModules] = useState<Module[]>([]);
  const [interactions, setInteractions] = useState<Interaction[]>([]);
  useEffect(() => {
    fetch('/modules').then(res => res.json()).then(setModules);
    fetch('/api/interactions').then(res => res.json()).then(setInteractions);
  }, []);
  return (
    <div>
      <div>
        {modules.map(m => <span key={m.name}>{m.name}</span>)}
      </div>
      <div>
        {interactions.map((i, idx) => (
          <div key={idx}>{`${i.input.module} → ${i.output.module}`}</div>
        ))}
      </div>
    </div>
  );
};

export default NodeMap; 