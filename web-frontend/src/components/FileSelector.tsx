import React, { useState, useEffect, useRef } from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  CircularProgress,
  Alert,
  Button,
  Paper
} from '@mui/material';

interface FileInfo {
  name: string;
  path: string;
  size: number;
}

interface FileSelectorProps {
  value: string;
  onChange: (value: string) => void;
  label: string;
  directory?: string;
  onFileUploaded?: (fileInfo: FileInfo) => void;
}

const AUDIO_EXTENSIONS = ['.wav', '.mp3', '.flac', '.aiff', '.ogg'];

const FileSelector: React.FC<FileSelectorProps> = ({
  value,
  onChange,
  label,
  directory = 'tests/Assets',
  onFileUploaded
}) => {
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadFiles = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/browse_files?dir=${encodeURIComponent(directory)}`);
      if (!response.ok) throw new Error('Failed to load files');
      const data = await response.json();
      setFiles(data.files || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load files');
      setFiles([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();
    // eslint-disable-next-line
  }, [directory]);

  const handleFileUpload = async (file: File) => {
    setUploading(true);
    setError(null);
    try {
      const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      if (!AUDIO_EXTENSIONS.includes(ext)) {
        setError('Unsupported file type');
        setUploading(false);
        return;
      }
      const formData = new FormData();
      formData.append('file', file);
      const response = await fetch(`/api/upload_file?dir=${encodeURIComponent(directory)}`, {
        method: 'POST',
        body: formData
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Upload failed');
      }
      const data = await response.json();
      const uploadedFile = data.file;
      await loadFiles();
      onChange(uploadedFile.path);
      if (onFileUploaded) onFileUploaded(uploadedFile);
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (selectedFiles && selectedFiles.length > 0) {
      handleFileUpload(selectedFiles[0]);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  if (loading) {
    return (
      <Box display="flex" alignItems="center" gap={1}>
        <CircularProgress size={16} />
        <Typography variant="caption">Loading files...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ my: 1 }}>{error}</Alert>
    );
  }

  return (
    <Box>
      <FormControl fullWidth size="small">
        <InputLabel>{label}</InputLabel>
        <Select
          value={value}
          label={label}
          onChange={e => onChange(e.target.value)}
          renderValue={selected => {
            if (!selected) return label;
            const selectedFile = files.find(f => f.path === selected);
            return selectedFile ? selectedFile.name : selected;
          }}
        >
          <MenuItem value="">
            <em>Select audio file...</em>
          </MenuItem>
          {files.length === 0 ? (
            <MenuItem disabled>
              <em>No files available</em>
            </MenuItem>
          ) : (
            files.map(file => (
              <MenuItem key={file.path} value={file.path}>
                {file.name}
              </MenuItem>
            ))
          )}
        </Select>
      </FormControl>
      <Box mt={1}>
        <Paper
          variant="outlined"
          sx={{ p: 2, textAlign: 'center', cursor: 'pointer', borderStyle: 'dashed' }}
          onClick={() => fileInputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={e => e.preventDefault()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={AUDIO_EXTENSIONS.join(',')}
            style={{ display: 'none' }}
            onChange={handleFileInput}
          />
          <Typography variant="body2" color="text.secondary">
            {uploading ? 'Uploading...' : 'Drag & drop audio file here or click to browse'}
          </Typography>
        </Paper>
      </Box>
    </Box>
  );
};

export default FileSelector; 