import React, { useState } from 'react'
import Form from 'react-bootstrap/Form';
import { useAuth } from '../context/AuthContext';

const InputFile = () => {
    const { user } = useAuth();
    const [uploading, setUploading] = useState(false);
    const [selectedImage, setSelectedImage] = useState("");
    const [selectedFile, setSelectedFile] = useState<File>();
    const [title, setTitle] = useState("");

    const handleUpload = async () => {
        setUploading(true);
        try {
            if (!selectedFile) throw new Error("No file selected");
            if (title == "") throw new Error("No title selected");
            const formData = new FormData;
            formData.append("file", selectedFile);
            const resp = await fetch(`http://localhost:8001/upload/${title}`, {
                method: "POST",
                headers: {
                    "Content-Type": "multipart/form-data",
                    "Authorization" : `Bearer ${user.idToken}`
                },
                body: formData,
            })
            console.debug(resp);
        } catch (error: any) {
            console.debug(error);
        }
        setUploading(false);
    };

    return (
        <div>
            <Form>
                <Form.Group className="mb-3" controlId="formTitle">
                    <Form.Label>Email address</Form.Label>
                    <Form.Control type="text" placeholder="Enter title" onChange={(event) => { setTitle(event.target.value) }} />
                    <Form.Text className="text-muted">
                        Title of the video
                    </Form.Text>
                </Form.Group>
                <Form.Group controlId="formFile" className="mb-3">
                    <Form.Label>Default file input example</Form.Label>
                    <Form.Control
                        type="file"
                        hidden
                        onChange={(event) => {
                            const target = event.target as HTMLInputElement;
                            if (target.files) {
                                const file = target.files[0];
                                setSelectedImage(URL.createObjectURL(file));
                                setSelectedFile(file);
                            }
                        }}
                    />
                </Form.Group>
            </Form>
            <button
                onClick={handleUpload}
                disabled={uploading}
                style={{ opacity: uploading ? ".5" : "1" }}
            >
                {uploading ? "Uploading.." : "Upload"}
            </button>
        </div>
    );
}

export default InputFile