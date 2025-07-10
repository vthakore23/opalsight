import React, { useState } from 'react';
import {
  Button,
  Menu,
  MenuItem,
  CircularProgress,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import {
  Download as DownloadIcon,
  InsertDriveFile as FileIcon,
  TableChart as ExcelIcon,
  Code as JsonIcon
} from '@mui/icons-material';

export default function ExportButton({ endpoint, filename, filters = {}, formats = ['csv', 'json', 'excel'] }) {
  const [anchorEl, setAnchorEl] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleExport = async (format) => {
    setLoading(true);
    handleClose();

    try {
      // Build query string
      const params = new URLSearchParams({ format, ...filters });
      const url = `${process.env.REACT_APP_API_URL || 'http://localhost:5000'}/api/export${endpoint}?${params}`;

      // Fetch the file
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Export failed');
      }

      // Get the blob
      const blob = await response.blob();

      // Create download link
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      
      // Set filename with proper extension
      const extension = format === 'excel' ? 'xlsx' : format;
      const downloadFilename = filename ? `${filename}.${extension}` : `export_${Date.now()}.${extension}`;
      link.download = downloadFilename;

      // Trigger download
      document.body.appendChild(link);
      link.click();
      link.remove();

      // Clean up
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getIcon = (format) => {
    switch (format) {
      case 'excel':
        return <ExcelIcon />;
      case 'json':
        return <JsonIcon />;
      default:
        return <FileIcon />;
    }
  };

  const getLabel = (format) => {
    switch (format) {
      case 'excel':
        return 'Excel (.xlsx)';
      case 'json':
        return 'JSON (.json)';
      case 'csv':
        return 'CSV (.csv)';
      default:
        return format.toUpperCase();
    }
  };

  return (
    <>
      <Button
        variant="outlined"
        startIcon={loading ? <CircularProgress size={20} /> : <DownloadIcon />}
        onClick={handleClick}
        disabled={loading}
      >
        Export
      </Button>
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
      >
        {formats.map((format) => (
          <MenuItem key={format} onClick={() => handleExport(format)}>
            <ListItemIcon>
              {getIcon(format)}
            </ListItemIcon>
            <ListItemText primary={getLabel(format)} />
          </MenuItem>
        ))}
      </Menu>
    </>
  );
} 