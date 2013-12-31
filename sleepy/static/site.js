(function() {
var API_PREFIX = "/api/v1/";
var $resource = $("select[name='resource']");

/** Return the URL inputted by the user. **/
var getUrl = function() {
    var resource = $resource.val();
    var pk = $("#primaryKey").val();
    var url = API_PREFIX + resource + "/";
    if (pk) {
        url +=  pk;
    };
    return url;
}

var toggleParams = function(resource) {
    var $itemParams = $("#itemParams")
    var $personParams = $("#personParams");
    if (resource === 'items'){
        $itemParams.show();
        $personParams.hide();
    } else if (resource === "people"){
        $itemParams.hide();
        $personParams.show();
    } else {
        $itemParams.hide();
        $personParams.hide();
    }
}

/** Functions for outputting the response to the user. **/

syntaxHighlight = function(json) {
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
        var cls = 'number';
        if (/^"/.test(match)) {
            if (/:$/.test(match)) {
                cls = 'key';
            } else {
                cls = 'string';
            }
        } else if (/true|false/.test(match)) {
            cls = 'boolean';
        } else if (/null/.test(match)) {
            cls = 'null';
        }
        return '<span class="' + cls + '">' + match + '</span>';
    });
}

var Display = {
    elem: $("#response code"),
    response: function(data){
        var json = JSON.stringify(data, undefined, 2)
        this.elem.html(syntaxHighlight(json));
    },
    error: function(status, msg){
        this.elem.text(status + ": " + msg);
    }
}


window.Request = {
    /**
     * Send a request of a certain type (GET, POST...) to the URL specified
     * in the inputs. Used by the public method (Request.get, Request.post...)
     */
    _sendRequest: function(type, payload) {
        $.ajax({
            type: type, url: getUrl(),
            dataType: "json", contentType: "application/json",
            data: JSON.stringify(payload),
            success: function(data) {
                Display.response(data);
            },
            error: function(xhr, status, errorThrown){
                Display.error(status, errorThrown);
            }
        });
    },

    /**
     * Construct the payload object from the user's input.
     */
    _getPayload: function() {
        var payload;
        var resource = $("select[name='resource']").val();
        if (resource === "items") {
            var name = $("input[name='name']").val();
            var personId = $("input[name='person_id']").val();
            var checkedOutVal = $("select[name='checked_out']").val();
            var checkedOut = checkedOutVal === "true";
            payload = {"name": name,
                        "person_id": personId,
                        "checked_out": checkedOut};
        } else if (resource === "people") {
            var firstname = $("input[name='firstname']").val();
            var lastname = $("input[name='lastname']").val();
            payload = {"firstname": firstname, "lastname": lastname};
        };
        return payload;
    },

    /** Request public methods **/
    get: function(){
        this._sendRequest("GET", {});
    },

    post: function() {
        var payload = this._getPayload();
        this._sendRequest("POST", payload);
    },

    delete: function() {
        this._sendRequest("DELETE", {});
    },

    put: function() {
        var payload = this._getPayload();
        this._sendRequest("PUT", payload);
    }
}

$(document).ready(function(){
    Request.get();
    // If selection is changed, show correct params and send
    // a get request to the endpoint
    $resource.on("change", function(event){
        var resource = $resource.val();
        toggleParams(resource);
        Request.get();
    })
})

}).call(this);
