import React, { useState, useEffect, useRef } from 'react';
import { TextField, Slider, Select, MenuItem, Box, Typography, CircularProgress, Snackbar, Alert } from '@mui/material';

interface ModuleSettingsFormProps {
  manifest: any;
  config: any;
  moduleId: string;
  onConfigChange?: (config: any) => void;
  persistOnChange?: boolean;
}

const ModuleSettingsForm: React.FC<ModuleSettingsFormProps> = ({ manifest, config, moduleId, onConfigChange, persistOnChange = true }) => {
  const [form, setForm] = useState({ ...config });
  const [audioFiles, setAudioFiles] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({ open: false, message: '', severity: 'success' });
  const dropRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setForm({ ...config });
  }, [config]);

  useEffect(() => {
    // Only fetch audio files if this module has a filepath field named file_path
    if (manifest.fields.some((f: any) => f.type === 'filepath' && f.name === 'file_path')) {
      fetch('/api/audio_files')
        .then(res => {
          if (!res.ok) throw new Error('Failed to fetch audio files');
          return res.json();
        })
        .then(setAudioFiles)
        .catch(err => {
          setSnackbar({ open: true, message: 'Error loading audio files: ' + err.message, severity: 'error' });
          setAudioFiles([]);
        });
    }
  }, [manifest]);

  const handleFieldChange = (name: string, value: any) => {
    const updated = { ...form, [name]: value };
    setForm(updated);
    if (onConfigChange) onConfigChange(updated);
    if (persistOnChange) {
      fetch(`/modules/${moduleId}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [name]: value }),
      });
    }
  };

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setUploading(true);
    const file = e.dataTransfer.files[0];
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch('/api/audio_files', { method: 'POST', body: formData });
      if (res.status === 409) {
        setSnackbar({ open: true, message: 'File already exists', severity: 'error' });
      } else if (!res.ok) {
        setSnackbar({ open: true, message: 'Upload failed', severity: 'error' });
      } else {
        setSnackbar({ open: true, message: 'File uploaded', severity: 'success' });
        fetch('/api/audio_files')
          .then(res => {
            if (!res.ok) throw new Error('Failed to fetch audio files after upload');
            return res.json();
          })
          .then(setAudioFiles)
          .catch(err => {
            setSnackbar({ open: true, message: 'Error loading audio files after upload: ' + err.message, severity: 'error' });
            setAudioFiles([]);
          });
      }
    } catch (err) {
      setSnackbar({ open: true, message: 'Upload failed', severity: 'error' });
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>{manifest.name} Settings</Typography>
      {manifest.fields.map((field: any) => {
        switch (field.type) {
          case 'text':
            return (
              <TextField
                key={field.name}
                label={field.label}
                value={form[field.name] ?? ''}
                onChange={e => handleFieldChange(field.name, e.target.value)}
                fullWidth
                margin="normal"
              />
            );
          case 'number':
            return (
              <TextField
                key={field.name}
                label={field.label}
                type="number"
                value={form[field.name] ?? ''}
                onChange={e => handleFieldChange(field.name, Number(e.target.value))}
                fullWidth
                margin="normal"
              />
            );
          case 'slider':
            return (
              <Box key={field.name} sx={{ my: 2 }}>
                <Typography gutterBottom>{field.label}: {form[field.name]}</Typography>
                <Slider
                  value={form[field.name] ?? field.default ?? 0}
                  min={field.min ?? 0}
                  max={field.max ?? 100}
                  step={field.step ?? 1}
                  onChange={(_, value) => handleFieldChange(field.name, value as number)}
                  valueLabelDisplay="auto"
                />
              </Box>
            );
          case 'filepath':
            return (
              <Box key={field.name} sx={{ my: 2 }}>
                <Typography gutterBottom>{field.label}</Typography>
                <Select
                  value={form[field.name] ?? ''}
                  onChange={e => handleFieldChange(field.name, e.target.value)}
                  sx={{ minWidth: 200 }}
                  displayEmpty
                >
                  {audioFiles.length === 0 && (
                    <MenuItem value="" disabled>
                      {snackbar.open && snackbar.severity === 'error' ? 'Error loading files' : 'No audio files found'}
                    </MenuItem>
                  )}
                  {audioFiles.map(f => <MenuItem key={f} value={f}>{f}</MenuItem>)}
                </Select>
                <Box
                  ref={dropRef}
                  onDrop={handleDrop}
                  onDragOver={e => e.preventDefault()}
                  sx={{ mt: 2, p: 2, border: '2px dashed #888', borderRadius: 2, textAlign: 'center', background: uploading ? '#222' : 'inherit' }}
                >
                  {uploading ? <CircularProgress /> : 'Drag and drop audio file here'}
                </Box>
              </Box>
            );
          case 'waveform':
            return (
              <Box key={field.name} sx={{ my: 2 }}>
                <Typography gutterBottom>{field.label}</Typography>
                {form.file_path ? (
                  <img
                    src={`/api/module_waveform/audio_output?file=${encodeURIComponent(form.file_path)}`}
                    alt="Waveform"
                    style={{ maxWidth: 400, border: '1px solid #444' }}
                  />
                ) : (
                  <Typography color="text.secondary">No file selected</Typography>
                )}
              </Box>
            );
          case 'time':
            return (
              <TextField
                key={field.name}
                label={field.label}
                type="time"
                value={form[field.name] ?? field.default ?? ''}
                onChange={e => handleFieldChange(field.name, e.target.value)}
                fullWidth
                margin="normal"
                InputLabelProps={{
                  shrink: true,
                }}
              />
            );
          default:
            return null;
        }
      })}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity={snackbar.severity} sx={{ width: '100%' }}>{snackbar.message}</Alert>
      </Snackbar>
    </Box>
  );
};

export default ModuleSettingsForm; 