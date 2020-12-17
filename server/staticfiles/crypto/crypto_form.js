/**
 * MC51 - clipster.cc
 * Encrypting and Decrypting Clips on Client side
 */

const HASH_ITERATIONS = 10000;
const SLEEP_BEFORE_SEND = 5000;
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

async function shareFormEncrypt(event) {
    /**
     *  When sharing clip encrypt first locally before transmitting to server
     */
    var username = event.target['username'].value;
    var password = event.target['password'].value;
    var clip_cleartext = event.target['id_text'].value;
    var valid = await isPasswordValid(username, password); // Wait for async response

    if (!valid) {
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

    for (i = 0; i < clips_encrypted.length; i++) {
        try {
            clips_cleartext[i] = decrypt(username, password, clips_encrypted[i]);
        } catch (e) {
            // Display error status
            clips_cleartext[i] = e;
            decrypt_errors = true;
        }
    }
    show_decrypted_clips(clips_cleartext, decrypt_errors);
}

function show_decrypted_clips(clips_cleartext, errors) {

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
        clips[i].innerHTML = clips_cleartext[i];
    }
}


function encrypt(username, password, clip_cleartext) {
    /**
     * Encrypt clip using PBKDF2 and Fernet
     * return: String - encrypted clip
     */

    // PBKDF2 Hash Key creation from SJCL lib
    var salt = "clipster_" + username + "_" + password;
    var derivedKey = sjcl.misc.pbkdf2(password, salt, HASH_ITERATIONS);
    var b64Key = sjcl.codec.base64url.fromBits(derivedKey);

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

    // PBKDF2 Hash Key creation from SJCL lib
    var salt = "clipster_" + username + "_" + password;
    var derivedKey = sjcl.misc.pbkdf2(password, salt, HASH_ITERATIONS);
    var b64Key = sjcl.codec.base64url.fromBits(derivedKey);
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