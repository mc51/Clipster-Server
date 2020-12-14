/**
 * MC51 - clipster.cc
 * Encrypting and Decrypting Clips on Client Cide
 */

var HASH_ITERATIONS = 10000;
var SLEEP_BEFORE_SEND = 5000;

async function shareFormEncrypt(event) {
    // When sharing clip encrypt first before transmitting to server
    // event.preventDefault();
    var username = event.target['username'].value;
    var password = event.target['password'].value;
    var clip_cleartext = event.target['id_text'].value;

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

    console.log(clip_cleartext);
    console.log(clip_encrypted);

    return true;
}


function listFormData(event) {
    event.preventDefault();
    var username = event.target['username'].value;
    var password = event.target['password'].value;

    var clips_encrypted = Array.prototype.slice.
        call(document.querySelectorAll('#clip_encrypted')).
        map(function (a) {
            return a.innerHTML.replace(/ /g, '').replace(/\n/g, '');
        });

    try {
        var clips_cleartext = decrypt(username, password, clips_encrypted);
        show_decrypted_clips(clips_cleartext);
    } catch (e) {
        // Display error status
        document.getElementById("crypto_status_msg").style["display"] = "block";
        document.getElementById("crypto_status_msg").style["color"] = "red";
        document.getElementById("crypto_status_msg").innerHTML = e;
    }
    console.log(clip_cleartext);
}

function show_decrypted_clips(clips_cleartext) {

    // Display success status
    document.getElementById("crypto_status_msg").style["display"] = "block";
    document.getElementById("crypto_status_msg").style["color"] = "";
    document.getElementById("crypto_status_msg").innerHTML = "Decrypted successfully";

    // Get table cols placeholders
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

function decrypt(username, password, clips_encrypted) {
    /**
     *  Decrypt the clips on the page using PBKDF2 and Fernet
     *  return: Array - Ecrypted strings
     */

    // PBKDF2 Hash Key creation from SJCL lib
    var salt = "clipster_" + username + "_" + password;
    var derivedKey = sjcl.misc.pbkdf2(password, salt, HASH_ITERATIONS);
    var b64Key = sjcl.codec.base64url.fromBits(derivedKey);

    // Use Key to De-/Encrypt via Fernet lib
    var secret = new fernet.Secret(b64Key);

    let clip_cleartext = []
    for (var i = 0; i < clips_encrypted.length; i++) {

        clip = clips_encrypted[i];
        console.log("Decrypting: " + clip);
        // Decrypt via Fernet
        var token = new fernet.Token({
            secret: secret,
            token: clip,
            ttl: 0
        });
        clip_cleartext[i] = token.decode();
    }
    return clip_cleartext;
}