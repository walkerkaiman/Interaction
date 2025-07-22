import { useState, useEffect, useRef } from 'react';
import { Card, CardActionArea, CardContent, Typography, Button, Select, MenuItem, Box, CircularProgress } from '@mui/material';
import ReactMarkdown from 'react-markdown';

const WikiPage = () => {
  const [modules, setModules] = useState<{ name: string }[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [markdown, setMarkdown] = useState<string>('');
  const [audioFiles, setAudioFiles] = useState<string[]>([]);
  const [selectedAudio, setSelectedAudio] = useState<string>('');
  const [uploading, setUploading] = useState(false);
  const dropRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch('/modules').then(res => res.json()).then(setModules);
  }, []);

  useEffect(() => {
    if (selected === 'audio_output') fetchAudioFiles();
  }, [selected]);

  const fetchAudioFiles = () => {
    fetch('/api/audio_files').then(res => res.json()).then(setAudioFiles);
  };

  const handleCardClick = (moduleName: string) => {
    fetch(`/api/module_wiki/${moduleName}`)
      .then(res => res.text())
      .then(setMarkdown);
    setSelected(moduleName);
  };

  const handleAudioChange = (e: any) => {
    const file = e.target.value;
    setSelectedAudio(file);
    // Update backend config for audio_output
    fetch('/modules/audio_output/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_path: file }),
    });
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setUploading(true);
    const file = e.dataTransfer.files[0];
    const formData = new FormData();
    formData.append('file', file);
    fetch('/api/audio_files', { method: 'POST', body: formData })
      .then(() => fetchAudioFiles())
      .finally(() => setUploading(false));
  };

  if (selected) {
    return (
      <div>
        <Button variant="outlined" onClick={() => setSelected(null)} sx={{ mb: 2 }}>Back to Wiki List</Button>
        {selected === 'audio_output' && (
          <div style={{ marginBottom: 16 }}>
            <Typography variant="subtitle1">Waveform Preview:</Typography>
            <img src={selectedAudio ? `/api/module_waveform/audio_output?file=${encodeURIComponent(selectedAudio)}` : '/api/module_waveform/audio_output'} alt="Waveform" style={{ maxWidth: 400, border: '1px solid #444' }} />
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2">Select Audio File:</Typography>
              <Select value={selectedAudio} onChange={handleAudioChange} sx={{ minWidth: 200 }}>
                {audioFiles.map(f => <MenuItem key={f} value={f}>{f}</MenuItem>)}
              </Select>
            </Box>
            <Box ref={dropRef} onDrop={handleDrop} onDragOver={e => e.preventDefault()} sx={{ mt: 2, p: 2, border: '2px dashed #888', borderRadius: 2, textAlign: 'center', background: uploading ? '#222' : 'inherit' }}>
              {uploading ? <CircularProgress /> : 'Drag and drop audio file here'}
            </Box>
          </div>
        )}
        <ReactMarkdown>{markdown}</ReactMarkdown>
      </div>
    );
  }

  return (
    <div>
      <Typography variant="h4" gutterBottom>Module Wiki</Typography>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16 }}>
        {modules.map((mod) => (
          <div key={mod.name} style={{ flex: '1 0 30%', minWidth: 250, maxWidth: 400 }}>
            <Card>
              <CardActionArea onClick={() => handleCardClick(mod.name)}>
                <CardContent>
                  <Typography variant="h6">{mod.name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</Typography>
                  <Typography variant="body2" color="text.secondary">wiki.md</Typography>
                </CardContent>
              </CardActionArea>
            </Card>
          </div>
        ))}
      </div>
    </div>
  );
};

export default WikiPage; 