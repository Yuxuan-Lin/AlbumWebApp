window.onload = () => {
    const apigClient = apigClientFactory.newClient({
        apiKey: 'nOtJl4WVzx3AkSIV9iHbb6EINzLmFQD462dWZJVQ'
    });

    // Upload image
    const fileInput = document.getElementById("myFile");
    fileInput.onchange = (event) => {
        const fileReader = new FileReader();
        fileReader.onload = (frEvent) => {
            document.getElementById("renderImage").innerHTML = '<center><img src="' + frEvent.target.result + '" /></center>';
        }
        fileReader.readAsDataURL(fileInput.files[0]);
    }
    const fileUploadBtn = document.getElementById("fileUploadBtn");
    fileUploadBtn.onclick = (event) => {
        if (!fileInput.files) {
            return;
        }

        handleFileReader(fileInput.files[0], (err, params, body) => {
            if (err) {
                console.log(err);
                return;
            }
            handleFileUpload(apigClient, params, body);
        });
    }

    // Search content
    const searchText = document.getElementById("searchText");
    searchText.addEventListener("keyup", (event) => {
        event.preventDefault();
        if (event.code == 'Enter') {
            handleSearchWithText(apigClient, searchText.value);
        }
    })

    let ready_for_recording;

    window.SpeechRecognition = window.webkitSpeechRecognition || window.SpeechRecognition
    if ('SpeechRecognition' in window) {
        console.log("SpeechRecognition is Working");
        ready_for_recording = true;
    } else {
        console.log("SpeechRecognition is Not Working");
        ready_for_recording = false;
    }

    var inputSearchQuery = document.getElementById("searchText");
    const recognition = new window.SpeechRecognition();
    //recognition.continuous = true;

    var micButton = document.getElementById("searchVoice");

    micButton.addEventListener('click', function () {
        if (ready_for_recording) {
            recognition.start();
        } else if (!ready_for_recording) {
            recognition.stop();
        }

        recognition.addEventListener("start", function () {
            ready_for_recording = false;
            console.log("Recording.....");
        });

        recognition.addEventListener("end", function () {
            console.log("Stopping recording.");
            ready_for_recording = true;
        });

        recognition.addEventListener("result", resultOfSpeechRecognition);
        function resultOfSpeechRecognition(event) {
            const current = event.resultIndex;
            transcript = event.results[current][0].transcript;
            inputSearchQuery.value = transcript;
            console.log("transcript : ", transcript)
            handleSearchWithText(apigClient, transcript)
        }
    });

};


function handleFileReader(file, callback) {
    const fileReader = new FileReader();
    const imgName = document.getElementById("imgName").value;
    // fileReader.onload = () => callback(null, fileReader.result);
    fileReader.onload = (event) => {
        console.log(file);
        console.log(fileReader);
        let body = event.target.result;
        let filename = imgName;
        let params = {
            folder: 'albumbucketkerwin2',
            object: filename,
            'Content-Type': file.type,
            'x-amz-meta-customLabels': imgName,
        };
        callback(null, params, body);
    }
    fileReader.onerror = (err) => callback(err);
    fileReader.readAsDataURL(file);
    // fileReader.readAsBinaryString(file);
}

function handleFileUpload(apigClient, params, body) {
    
    let additionalParams = {};
    apigClient.uploadFolderObjectPut(params, body, additionalParams)
        .then((res) => {
            console.log(res);
            // Clean up webpage
            document.getElementById("imgName").value = "";
            document.getElementById("myFile").value = '';
            document.getElementById("renderImage").innerHTML = '';
        })
        .catch((err) => {
            console.log(err);
        });
}

function handleSearchWithText(apigClient, text) {
    console.log(text);
    if (!imgName) {
        return;
    }
    let params = {
        q: text
    };
    let body = {};
    let additionalParams = {};
    apigClient.searchGet(params, body, additionalParams)
            .then((res) => {
                console.log(res);

                let image_list = document.getElementById("images-list");

                image_list.innerHTML = "";

                for (let i = 0; i < res.data.encoded_image.length; i++) {
                    let img_data;
                    if (res.data.encoded_image[i].startsWith('data')) {
                        img_data = res.data.encoded_image[i]
                    } else {
                        img_data = "data:image/png;base64," + res.data.encoded_image[i]
                    }
                    let image = new Image();
                    image.src = img_data;
                    let img = document.createElement('li');
                    img.appendChild(image);
                    image_list.appendChild(img);
                }

                // TODO: show image
                // document.getElementById("searchText").value = "";
            })
            .catch((err) => {
                console.log(err);
            });
    
}

// function addPhoto(albumName) {
//     var files = document.getElementById("photoupload").files;
//     if (!files.length) {
//       return alert("Please choose a file to upload first.");
//     }
//     var file = files[0];
//     var fileName = file.name;
//     var albumPhotosKey = encodeURIComponent(albumName) + "/";
  
//     var photoKey = albumPhotosKey + fileName;
  
//     // Use S3 ManagedUpload class as it supports multipart uploads
//     var upload = new AWS.S3.ManagedUpload({
//       params: {
//         Bucket: albumBucketName,
//         Key: photoKey,
//         Body: file
//       }
//     });
  
//     var promise = upload.promise();
  
//     promise.then(
//       function(data) {
//         alert("Successfully uploaded photo.");
//         viewAlbum(albumName);
//       },
//       function(err) {
//         return alert("There was an error uploading your photo: ", err.message);
//       }
//     );
//   }

function base64ToBlob(base64, mime) {
    mime = mime || "";
    var sliceSize = 1024;
    var byteChars = window.atob(base64);
    var byteArrays = [];

    for (var offset = 0, len = byteChars.length; offset < len; offset += sliceSize) {
        var slice = byteChars.slice(offset, offset + sliceSize);

        var byteNumbers = new Array(slice.length);
        for (var i = 0; i < slice.length; i++) {
            byteNumbers[i] = slice.charCodeAt(i);
        }

        var byteArray = new Uint8Array(byteNumbers);

        byteArrays.push(byteArray);
    }

    return new Blob(byteArrays, { type: mime });
}

function loadBinaryResource(url) {
    const req = new XMLHttpRequest();
    req.open("GET", url, false);
  
    // XHR binary charset opt by Marcus Granado 2006 [http://mgran.blogspot.com]
    req.overrideMimeType("text/plain; charset=x-user-defined");
    req.send(null);
    return req.status === 200 ? req.responseText : "";
}

