/**
 * MC51 - clipster.cc
 * Encrypting and Decrypting Clips on Client side
 */

const HASH_ITER_LOGIN = 20000;
const HASH_ITER_MSG = 10000;
const MIN_PW_LENGTH = 8;

const API_USER_VERIFY = "/verify-user/";

const isPasswordValid = async (username, password) => {
    /**
    * Check credentials against API using HTTPBasicAuth Get Request
    */
    var response = await fetch(API_USER_VERIFY, {
        method: "GET",
        // Dont send cookies, otherwise this will return 200 as we're logged in already
        credentials: "omit",
        headers: {
            "Authorization": "Basic " + btoa(username + ":" + password)
        }
    });

    if (response.ok) {
        console.log("Authenticated");
        return true;
    } else {
        console.log("Could not authenticate");
        return false;
    }
};

function pwToHashRegister(event) {
    /**
     * In Register Form hash pw before sending to server
     */
    var username = event.target['username'].value;
    var password1 = event.target['password1'].value;
    var password2 = event.target['password2'].value;
    var password = password1;

    if (password1 != password2) {
        console.log("Passwords do not match!")
        return true;
    }

    if (password1.length < MIN_PW_LENGTH) {
        console.log("Password is too short!")
        return true;
    }

    var b64Key = pwToHashForAuth(username, password);

    console.log("PW Hash: " + b64Key);

    document.getElementById("id_password1").value = b64Key;
    document.getElementById("id_password2").value = b64Key;
    return true;
}


function pwToHashLogin(event) {
    /**
     * In Login Form hash pw before sending to server
     */
    var username = event.target['username'].value;
    var password = event.target['password'].value;

    var b64Key = pwToHashForAuth(username, password);

    console.log("PW Hash: " + b64Key);
    document.getElementById("id_password").value = b64Key;
    return true;
}

function pwToHashForAuth(username, password) {
    /**
     * Get PBKDF2 hash for password
     */
    var salt = "clipster_" + username + "_" + password;
    var derivedKey = sjcl.misc.pbkdf2(password, salt, HASH_ITER_LOGIN);
    var b64Key = sjcl.codec.base64.fromBits(derivedKey, false, true); // with = padding and urlSafe
    console.log("PW Hash: " + b64Key);
    return b64Key;
}

function pwToHashForMsg(username, password) {
    /**
     * Get PBKDF2 hash for password
     */
    var salt = "clipster_" + username + "_" + password;
    var derivedKey = sjcl.misc.pbkdf2(password, salt, HASH_ITER_MSG);
    console.log("Derived Key: " + derivedKey);
    var b64Key = sjcl.codec.base64.fromBits(derivedKey, false, true); // with = padding and urlSafe
    console.log("PW Hash: " + b64Key);
    return b64Key;
}


async function shareFormEncrypt(event) {
    /**
     *  When sharing clip encrypt first locally before transmitting to server
     *  Check Login for Hashed PW
     */
    var username = event.target['username'].value;
    var password = event.target['password'].value;
    var clip_cleartext = event.target['id_text'].value;

    pw_login_hash = pwToHashForAuth(username, password);
    var valid = await isPasswordValid(username, pw_login_hash); // Wait for async response

    if (!valid) {
        // Password could not be checked, show error message and stop
        document.getElementById("share_status_msg").style["display"] = "block";
        document.getElementById("share_status_msg").style["color"] = "red";
        document.getElementById("share_status_msg").innerHTML = "Error: Wrong password"
        return false;
    }
    try {
        var clip_encrypted = encrypt(username, password, clip_cleartext);
        // Display success status
        document.getElementById("share_status_msg").style["display"] = "block";
        document.getElementById("share_status_msg").style["color"] = "";
        document.getElementById("share_status_msg").innerHTML = "Encrypted successfully";
        document.getElementById("id_text").value = clip_encrypted;
    } catch (e) {
        // Display error status
        document.getElementById("share_status_msg").style["display"] = "block";
        document.getElementById("share_status_msg").style["color"] = "red";
        document.getElementById("share_status_msg").innerHTML = e;
        return false;
    }

    // When all went fine, submit
    document.forms["share_clip_form"].submit();
}


function decryptClipList(event) {
    /**
     * Get all clips on page and decrypt them
     */

    var username = event.target['username'].value;
    var password = event.target['password'].value;
    var clips_cleartext = [];
    var decrypt_errors = false;

    var clips_encrypted = Array.prototype.slice.
        call(document.querySelectorAll('#clip_encrypted')).
        map(function (a) {
            return a.innerHTML.replace(/ /g, '').replace(/\n/g, '');
        });

    // get format info from class parameter's value
    var clips_format = Array.prototype.slice.
        call(document.querySelectorAll('#clip_encrypted')).
        map(function (a) {
            return a.className;
        });

    for (i = 0; i < clips_encrypted.length; i++) {
        try {
            clips_cleartext[i] = decrypt(username, password, clips_encrypted[i]);
        } catch (e) {
            // Display error status
            clips_cleartext[i] = e;
            decrypt_errors = true;
        }
    }
    show_decrypted_clips(clips_cleartext, clips_format, decrypt_errors);
}

function show_decrypted_clips(clips_cleartext, clips_format, errors) {

    // Display decryption status
    if (errors) {
        document.getElementById("crypto_status_msg").style["display"] = "block";
        document.getElementById("crypto_status_msg").style["color"] = "red";
        document.getElementById("crypto_status_msg").innerHTML =
            "Error: Some Clips could not be decrypted. Check your password";

    } else {
        document.getElementById("crypto_status_msg").style["display"] = "block";
        document.getElementById("crypto_status_msg").style["color"] = "";
        document.getElementById("crypto_status_msg").innerHTML = "OK: Decrypted successfully";
    }

    // Get table cols placeholders and replace with result
    var clips = Array.prototype.slice.
        call(document.querySelectorAll('#clip_cleartext')).
        map(function (a) {
            return a;
        });

    for (i = 0; i < clips.length; i++) {
        if (clips_format[i] == "img") {
            // display image
            clips[i].innerHTML = '<img class="thumb" src="data:image/png;base64,' + clips_cleartext[i] + '"></img>'
        } else {
            clips[i].innerHTML = clips_cleartext[i];
        }

    }
}


function encrypt(username, password, clip_cleartext) {
    /**
     * Encrypt clip using PBKDF2 and Fernet
     * return: String - encrypted clip
     */

    var b64Key = pwToHashForMsg(username, password);
    // Use Key to De-/Encrypt via Fernet lib
    var secret = new fernet.Secret(b64Key);
    var token = new fernet.Token({ secret: secret });
    var encrypted_clip = token.encode(clip_cleartext);
    return encrypted_clip;
}

function decrypt(username, password, clip_encrypted) {
    /**
     *  Decrypt the clip using PBKDF2 and Fernet
     *  return: clip_cleartext -  Decrypted string
     */

    var b64Key = pwToHashForMsg(username, password);
    var clip_cleartext;

    // Use Key to De-/Encrypt via Fernet lib
    var secret = new fernet.Secret(b64Key);
    var token = new fernet.Token({
        secret: secret,
        token: clip_encrypted,
        ttl: 0
    });
    clip_cleartext = token.decode();
    return clip_cleartext;
}

function encodeFileToBase64(elm) {
    /**
     *  On Image choice convert file to b64 string and add it to text
     *  Also set format to img
     */
    var file = elm.files[0];
    var imgReader = new FileReader();
    imgReader.onloadend = function () {
        // console.log('Base64 Format', imgReader.result);
        document.getElementById("id_format").value = "img";
        document.getElementById("id_text").value = imgReader.result.replace(/^data:.+;base64,/, '');
        document.getElementById("id_text").setAttribute('readonly', true);

        // status
        document.getElementById("share_status_msg").style["display"] = "block";
        document.getElementById("share_status_msg").style["color"] = "";
        document.getElementById("share_status_msg").innerHTML = "Image added as Clip!";
    }
    imgReader.readAsDataURL(file);
}

function resetForm() {
    // Reset all Inputs in Form to default
    console.log("Resetting form")
    document.getElementById("id_format").value = "txt";
    document.getElementById("fileupload").value = '';
    document.getElementById("id_text").value = '';
    document.getElementById("id_text").removeAttribute('readonly');
    document.getElementById("share_status_msg").innerHTML = "";
}