import React, { useEffect, useState, useRef } from 'react';
import { Box, Select, MenuItem, InputLabel, FormControl, Button, Typography, Paper, CircularProgress } from '@mui/material';

interface FileSelectorProps {
  directory: string;
  value?: string;
  onChange: (file: string) => void;
}

interface FileInfo {
  name: string;
  path: string;
  size: number;
}

const FileSelector: React.FC<FileSelectorProps> = ({ directory, value, onChange }) => {
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchFiles = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`http://localhost:8000/api/browse_files?dir=${encodeURIComponent(directory)}`);
      const data = await response.json();
      if (data.files) {
        setFiles(data.files);
      } else {
        setFiles([]);
      }
    } catch (e) {
      setError('Failed to load files');
      setFiles([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
    // eslint-disable-next-line
  }, [directory]);

  const handleFileSelect = (event: any) => {
    onChange(event.target.value as string);
  };

  const handleDrop = async (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
      await uploadFile(event.dataTransfer.files[0]);
    }
  };

  const handleFileInput = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      await uploadFile(event.target.files[0]);
    }
  };

  const uploadFile = async (file: File) => {
    setUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await fetch(`http://localhost:8000/api/upload_file?dir=${encodeURIComponent(directory)}`, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (data.success && data.file) {
        await fetchFiles();
        onChange(data.file.path);
      } else {
        setError(data.error || 'Upload failed');
      }
    } catch (e) {
      setError('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  return (
    <Box>
      <FormControl fullWidth size="small" sx={{ mb: 1 }}>
        <InputLabel id="file-selector-label">Select File</InputLabel>
        <Select
          labelId="file-selector-label"
          value={value || ''}
          label="Select File"
          onChange={handleFileSelect}
          disabled={loading || uploading}
        >
          {files.map(file => (
            <MenuItem key={file.path} value={file.path}>{file.name}</MenuItem>
          ))}
        </Select>
      </FormControl>
      <Paper
        variant="outlined"
        sx={{ p: 2, textAlign: 'center', background: '#fafafa', borderStyle: 'dashed', mb: 1, cursor: 'pointer' }}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onClick={() => fileInputRef.current?.click()}
      >
        <Typography variant="body2" color="textSecondary">
          Drag and drop a file here, or click to select
        </Typography>
        <input
          type="file"
          style={{ display: 'none' }}
          ref={fileInputRef}
          onChange={handleFileInput}
          disabled={uploading}
        />
        {uploading && <CircularProgress size={24} sx={{ mt: 1 }} />}
      </Paper>
      {error && <Typography color="error" variant="body2">{error}</Typography>}
    </Box>
  );
};

export default FileSelector; 