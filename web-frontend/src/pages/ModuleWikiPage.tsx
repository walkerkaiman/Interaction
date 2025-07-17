import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography, CircularProgress, Alert, Paper, TextField, Button } from '@mui/material';
import { getModuleNotes, saveModuleNotes } from '../api/api';

const getWikiUrl = (id: string) => `/module_wikis/${id}.md`;

const ModuleWikiPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [content, setContent] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Installation Notes state
  const [notes, setNotes] = useState<string>('');
  const [notesLoading, setNotesLoading] = useState<boolean>(true);
  const [notesError, setNotesError] = useState<string | null>(null);
  const [notesSaving, setNotesSaving] = useState<boolean>(false);
  const [notesSaved, setNotesSaved] = useState<boolean>(false);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError(null);
    fetch(getWikiUrl(id))
      .then((res) => {
        if (!res.ok) throw new Error('Wiki not found');
        return res.text();
      })
      .then((text) => {
        setContent(text);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [id]);

  useEffect(() => {
    if (!id) return;
    setNotesLoading(true);
    setNotesError(null);
    getModuleNotes(id)
      .then((data) => {
        setNotes(data || '');
        setNotesLoading(false);
      })
      .catch((err) => {
        setNotesError('Failed to load notes');
        setNotesLoading(false);
      });
  }, [id]);

  // Simple markdown to HTML (replace with a real renderer if needed)
  function renderMarkdown(md: string) {
    // Only basic formatting for now
    return md
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/\*\*(.*?)\*\*/gim, '<b>$1</b>')
      .replace(/\*(.*?)\*/gim, '<i>$1</i>')
      .replace(/\n/g, '<br />');
  }

  // Replace Installation Notes section with editable field
  function renderWikiWithEditableNotes(md: string) {
    const parts = md.split(/## Installation Notes/i);
    const before = parts[0] || '';
    // Everything after the heading is replaced by the editable field
    return (
      <>
        <div dangerouslySetInnerHTML={{ __html: renderMarkdown(before) }} />
        <Typography variant="h5" sx={{ mt: 4, mb: 2 }}>Installation Notes</Typography>
        {notesLoading ? (
          <CircularProgress />
        ) : notesError ? (
          <Alert severity="error">{notesError}</Alert>
        ) : (
          <Box sx={{ mb: 2 }}>
            <TextField
              label="Installation Notes"
              multiline
              minRows={4}
              maxRows={12}
              fullWidth
              value={notes}
              onChange={e => { setNotes(e.target.value); setNotesSaved(false); }}
              variant="outlined"
            />
            <Box sx={{ mt: 1, display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                color="primary"
                disabled={notesSaving}
                onClick={async () => {
                  setNotesSaving(true);
                  setNotesError(null);
                  try {
                    await saveModuleNotes(id!, notes);
                    setNotesSaved(true);
                  } catch (err) {
                    setNotesError('Failed to save notes');
                  } finally {
                    setNotesSaving(false);
                  }
                }}
              >
                Save
              </Button>
              {notesSaved && <Typography color="success.main" sx={{ alignSelf: 'center' }}>Saved!</Typography>}
            </Box>
          </Box>
        )}
      </>
    );
  }

  return (
    <Box p={4}>
      <Typography variant="h4" gutterBottom>
        {id ? `Module Wiki: ${id}` : 'Module Wiki'}
      </Typography>
      {loading && <CircularProgress />}
      {error && <Alert severity="error">{error}</Alert>}
      {!loading && !error && (
        <Paper elevation={2} sx={{ mt: 2, p: 3 }}>
          {renderWikiWithEditableNotes(content)}
        </Paper>
      )}
    </Box>
  );
};

export default ModuleWikiPage; 