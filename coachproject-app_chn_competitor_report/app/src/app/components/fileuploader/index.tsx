'use client';
import { useAppConfigContext } from '@/app/appcontext/appConfig';
import axios from 'axios';
import React, { useEffect, useState } from 'react';
import Icons from '../svgicons';

type FileData = {
  file: File;
  progress: number;
  isUploaded: boolean;
};

interface FileUploaderProp {
  closeUploader: () => void;
  continueUpload: (uploadingFile: any) => void;
  emptyFolder?: boolean;
  uploaderId?: string;
  uploaderTitle: string;
  uploadEndPoint?: string
}

const FileUploader: React.FC<FileUploaderProp> = ({
  closeUploader,
  continueUpload,
  emptyFolder,
  uploaderId = '',
  uploaderTitle,
  uploadEndPoint
}) => {
  const [files, setFiles] = useState<FileData[]>([]);
  const { envVal, destinationUrl } = useAppConfigContext();
  const [showUploadSection, setShowUploadSection] = useState(false);
  const [showFileSubmitted, setShowFileSubmitted] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!emptyFolder) {
      setShowUploadSection(true);
    }
  }, [emptyFolder]);

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const newFiles = Array.from(e.dataTransfer.files);
    addFiles([newFiles[0]]);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      addFiles(newFiles);
    }
  };

  const addFiles = (newFiles: File[]) => {
    setErrorMessage(null);
    const validFiles: FileData[] = [];
    const invalidFiles: string[] = [];

    newFiles.forEach((file) => {
      if (
        (file.type === 'application/pdf' ||
          file.type === 'application/vnd.ms-excel' ||
          file.type.includes('spreadsheet')) &&
        file.size <= 200 * 1024 * 1024 // 200MB
      ) {
        validFiles.push({
          file,
          progress: 0,
          isUploaded: false,
        });
      } else {
        invalidFiles.push(file.name);
      }
    });

    if (invalidFiles.length > 0) {
      setErrorMessage(`Invalid file format: ${invalidFiles.join(', ')}`);
    }

    setFiles(validFiles);
  };

  const updateProgressForFile = (index: number, percent: number) => {
    setFiles((prevFiles) => {
      const updated = [...prevFiles];
      updated[index] = {
        ...updated[index],
        progress: percent,
      };
      return updated;
    });
  };

  const uploadFiles = async () => {
    setShowFileSubmitted(true);
    const currentFiles = [...files];

    currentFiles.forEach(async (fileData, index) => {
      const formData = new FormData();
//       /upload-inhouse-sales -> KS Monthly Sales
// /upload-sales-statistics -> Upload Quarterly Store Count
      formData.append('user_file', fileData.file);
      formData.append('endpoint', uploadEndPoint ?? '/upload-list' );
      formData.append('destinationEnvLink', destinationUrl);

      try {
        const response = await axios.post('/api/uploadfile', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const percent = Math.round(
              (progressEvent.loaded * 100) / (progressEvent.total || 1)
            );
            updateProgressForFile(index, percent);
          },
        });

        if (response?.data?.status) {
          updateProgressForFile(index, 100);
        }
      } catch (error) {
        updateProgressForFile(index, 0);
        if (axios.isAxiosError(error)) {
          setErrorMessage(String(error?.response?.data?.error));
        }
      } finally {
        setShowFileSubmitted(false);
      }
    });
  };

  const handleCloseFileUploader = () => {
    setFiles([]);
    setErrorMessage(null);
    setShowFileSubmitted(false);
    closeUploader();
  };

  return (
    <div className='fileuploadercontainer h-full flex items-center justify-center'>
      <div className='file-upload-component bg-white border-[1px] border-[--D0D5DD] p-5 rounded-2xl shadow-md w-full min-w-md mx-auto'>
        <h3 className='text-lg font-semibold text-[--221D3E] mb-16'>{uploaderTitle}</h3>
        <div className='filuploadimg mb-4 flex justify-center flex-column item-center'>
          <Icons.FIleUploaderImg />
        </div>

        <div className='headings text-center w-full m-auto'>
          <h5 className='text-[--221D3E] text-lg font-bold'>Start by uploading file</h5>
          <p className='text-base text-[--221D3E] mb-5'>
            No data to show, please upload data to proceed.
          </p>
        </div>

          <>
            <div
              className={`drag-drop-box border-[1px] border-[--D0D5DD] rounded-xl p-4 text-center w-full h-32 m-auto ${
                showFileSubmitted ? 'cursor-not-allowed' : 'cursor-pointer'
              }`}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleFileDrop}
            >
              <div className='flex justify-center'>
                <Icons.InnerUploadIcon />
              </div>
              <input
                type='file'
                accept='.xls,.xlsx'
                className='hidden'
                onChange={handleFileSelect}
                id={`file-input-${uploaderId}`}
                disabled={showFileSubmitted}
              />
              <label
                htmlFor={`file-input-${uploaderId}`}
                className={`text-sm ${showFileSubmitted ? 'cursor-not-allowed' : 'cursor-pointer'}`}
              >
                <strong className='text-[--221D3E]'>Click to upload</strong>{' '}
                <span className='text-[#475467]'>or drag and drop your file here</span>
              </label>
              <p className='text-xs text-[#475467]'>
                Only PDF or Excel file is allowed (max 200MB).
              </p>
            </div>

            {files.map((fileData, index) => (
              <div
                key={index}
                className='file-list border-[1px] border-[--D0D5DD] overflow-hidden rounded-xl w-full m-auto flex items-center mt-5'
              >
                <div className='fileholder bg-[#F9FAFB] flex items-start p-4 gap-4 w-10/12'>
                  <div className='iconholder'>
                    <Icons.FileIcon />
                  </div>
                  <div className='filedetail text-sm flex flex-col'>
                    <span className='file-name font-bold text-[#344054]'>
                      {fileData.file.name}
                    </span>
                    <span className='file-size text-[#475467]'>
                      {Math.round(fileData.file.size / 1000)} kb{' '}
                      {fileData.progress > 0 && (
                        <span> – {fileData.progress}% uploaded</span>
                      )}
                    </span>
                  </div>
                </div>
                <div className='filestatus w-2/12 p-4 flex justify-end'>
                  {fileData.progress > 0 && fileData.progress < 100 ? (
                    <Icons.FileUploadingLoader />
                  ) : fileData.progress === 100 ? (
                    <Icons.FileUploadSuccess />
                  ) : null}
                </div>
              </div>
            ))}

            {errorMessage && (
              <div className='w-full m-auto rounded-md bg-red-500 text-white p-1 text-sm mt-2 text-center'>
                {errorMessage}
              </div>
            )}
          </>
        

          <div className='action-buttons mt-4 flex justify-center items-center gap-3 w-full m-auto'>
            <button
              className={`attach-button w-full bg-[--221D3E] text-white h-10 px-2 rounded-lg ${
                files.length === 0 ? 'cursor-not-allowed' : ''
              } ${showFileSubmitted ? 'opacity-80' : ''}`}
              disabled={files.length === 0 || showFileSubmitted}
              onClick={uploadFiles}
            >
              Attach File
            </button>
          </div>
  
      </div>
    </div>
  );
};

export default FileUploader;
