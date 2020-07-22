const reqURL = window.location;
const Http = new XMLHttpRequest();
var data;
//Calls queries endpoint
Http.open("GET",reqURL + "queries");
Http.send();
Http.onreadystatechange = function(){
    if(Http.readyState == 4){
        var raw = Http.responseText;
        console.log(raw);
        data = JSON.parse(raw);
        var keys = Object.keys(data);
        keys.forEach(PopulateTickets);
    }
};
//Populates the page one form at a time
//each ticket ends up becoming its own form
function PopulateTickets(_key){
    var form =document.createElement("form");
    form.classList.add("centerForm");
    form.setAttribute("method", "post")
    form.setAttribute("action",reqURL + "resolve/" + _key);
    var poster = document.createElement("h2");
    poster.innerHTML=data[_key]["poster"]
    var query =document.createElement("p");
    query.innerHTML=data[_key]["query"]
    var container = document.createElement("div");
    container.classList.add("btnContainer")
    var submit = document.createElement("input");
    submit.setAttribute("type","submit");
    submit.setAttribute("value","Resolve");
    container.appendChild(submit);
    form.appendChild(poster);
    form.appendChild(query);
    form.appendChild(container);

    document.getElementsByTagName('body')[0].appendChild(form);
}