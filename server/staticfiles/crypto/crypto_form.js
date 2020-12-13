/**
 * MC51 - clipster.cc
 * Encrypting and Decrypting Clips on Client Cide
 */

function getFormData(event) {
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
    // TODO: Functionality to encrypt clip before we submit it to server

    // PBKDF2 Hash Key creation from SJCL lib
    var salt = "clipster_" + username + "_" + password;
    var derivedKey = sjcl.misc.pbkdf2(password, salt, 10000);
    var b64Key = sjcl.codec.base64url.fromBits(derivedKey);

    // Use Key to De-/Encrypt via Fernet lib
    var secret = new fernet.Secret(b64Key);
    // var token = new fernet.Token({ secret: secret });
    // var ecrypted_msg = token.encode(secret_msg);
}

function decrypt(username, password, clips_encrypted) {
    /**
     *  Decrypt the clips on the page using PBKDF2 and Fernet
     *  return: Array - Ecrypted strings
     */

    // PBKDF2 Hash Key creation from SJCL lib
    var salt = "clipster_" + username + "_" + password;
    var derivedKey = sjcl.misc.pbkdf2(password, salt, 10000);
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