function getAllStatus() {
    fetch("/status")
}

function getRoot() {
    fetch("/")
}

function getStatus() {
    fetch("/" + $('#index_name').val() + "/status")
}

function search() {
    queryString = ""
    if($.trim($('#keywords').val())) {
        queryString += "q=" + $('#keywords').val()
    }
    if($.trim($('#serviceTypes').val())) {
        if(queryString) {
            queryString += "&"
        }
        queryString += "serviceTypes=" + $('#serviceTypes').val()
    }
    if($.trim($('#lot').val())) {
        if(queryString) {
            queryString += "&"
        }
        queryString += "lot=" + $('#lot').val()
    }
    fetch("/" + $('#search_index_name').val() + "/" + $('#search_index_type').val() + "/search?" + encodeURI(queryString))
}

function createIndex(){
    submit("/" + $('#create_index_name').val(), {}, "PUT")
}

function indexService(){
    submit(
        "/" + $('#index_doc_index_name').val() + "/" + $('#index_doc_index_type').val() + "/" + $('#index_doc_id').val(),
        $('#index_doc_json').val(),
        "POST")
}

function deleteIndex(){
    submit("/" + $('#delete_index_name').val(), {}, "DELETE")
}

function fetch(url) {
    var request = $.ajax({
           url: url,
           type: "GET",
           contentType: "application/json",
           headers: commonHeaders()
           });
    request.fail(function (jqXHR, textStatus, errorThrown){
             var obj = JSON.parse(jqXHR.responseText);
             $("#response").html(printHTMLResponse(jqXHR, obj));
         });
    request.done(function (response, textStatus, jqXHR){
              var obj = JSON.parse(jqXHR.responseText);
              $("#response").html(printHTMLResponse(jqXHR, obj));
         });
}

function submit(url, data, method) {
  var request = $.ajax({
           url: url,
           type: method,
           data : data,
           headers: commonHeaders("application/json")
           });
    request.fail(function (jqXHR, textStatus, errorThrown){
             var obj = JSON.parse(jqXHR.responseText);
             $("#response").html(printHTMLResponse(jqXHR, obj));
         });
    request.done(function (response, textStatus, jqXHR){
             var obj = JSON.parse(jqXHR.responseText);
             $("#response").html(printHTMLResponse(jqXHR, obj));
         });
}

function commonHeaders(contentType) {
    var headers = {}

    headers['Authorization'] = 'Bearer ' + $('#bearer-token').val();
    headers['Access-Control-Allow-Origin'] = "*";

    if (contentType != null) {
        headers['Content-type'] = contentType
    }

    return headers;
}

function printHTMLResponse(jqXHR, obj) {
    return "<i><h5>Response Status:</h5> " +  jqXHR.status +
           "<p/><h5>Response Headers:</h5><pre>" + jqXHR.getAllResponseHeaders() +
           "</pre><h5>Response Body:</h5><pre>" + JSON.stringify(obj, null, 4) + "</pre></i>"

}