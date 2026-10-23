"use client"

import FileUploader from "../components/fileuploader";

const ListUploader = () => {

  const closeUploader = () => {
    
  };

  const continueUpload = (fileData: any) => {
    console.log(fileData)
  }

  return (
    <div className="bg-fbfbfb">
      <div className=" bg-[#C1C1C11A] flex flex-wrap gap-5 p-5 mx-20 my-6 items-start rounded-2xl">
        <div className="w-[calc(50%-10px)]">
          <FileUploader  
            uploaderId="A" 
            closeUploader={closeUploader} 
            continueUpload={continueUpload} 
            uploaderTitle={'Upload KS Monthly Sales'}
            emptyFolder={true} 
            uploadEndPoint={'/upload-inhouse-sales'}
          />
        </div>
        <div className="w-[calc(50%-10px)]">
          <FileUploader 
            uploaderId="B"
            closeUploader={closeUploader} 
            continueUpload={continueUpload} 
            uploaderTitle={'Upload Quarterly Store Count'}
            emptyFolder={true} 
            uploadEndPoint={'/upload-sales-statistics'}
          />
        </div>
        <div className="w-[calc(50%-10px)]">
          <FileUploader 
            uploaderId="C"
            closeUploader={closeUploader} 
            continueUpload={continueUpload} 
            uploaderTitle={'Competitor Sales Data'}
            emptyFolder={true} 
            uploadEndPoint={'/upload-list'}
          />
        </div>
        <div className="w-[calc(50%-10px)]">
          <FileUploader 
            uploaderId="D"
            closeUploader={closeUploader} 
            continueUpload={continueUpload} 
            uploaderTitle={'Upload cls_pce_ss_deletion_list'}
            emptyFolder={true} 
            uploadEndPoint={'/upload-sku-list'}
          />
        </div>
      </div>
    </div>
  );
};

export default ListUploader;
