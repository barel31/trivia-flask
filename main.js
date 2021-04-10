function editScore(name, score, id) {
    var x = prompt("Enter score to user: "+name, score.toString());
    if (x == null || x == "") {
        return false;
    } if (isNaN(x)) {
        return false;
    } else {
        document.getElementById("admin_edit_score_btn"+id).value = id+"#"+x;
    }
}

function editName(name, id) {
    var x = prompt("Edit Nickname to user: "+name, name);
    if (x == null || x == "") {
        return false;
    } else {
        document.getElementById("admin_edit_name_btn"+id).value = id+"#"+x;
    }
}

if (window.history.replaceState) {
    window.history.replaceState(null, null, window.location.href);
}

function RequestMethod(arg) {
    fetch("/request-test", {
    method: "POST",
    body: JSON.stringify( arg: arg)},
    }).then((_res) => {
    window.location.href = "/";
    });
}