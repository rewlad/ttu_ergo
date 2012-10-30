
//Browser.msgBox('TEST');

var options = {};
options.method = "post";
options.headers = {'Content-Type':'application/json'};

//for(var j=0;j<l.length;j++)f(j,l[j])

values.forEach(function(row,rn,rows){
    row.forEach(function(v,cn,cells){
        if(v instanceof Date) cells[cn] = 
            v.getYear()+'-'+(v.getMonth()+1)+'-'+v.getDate()
    })
})



options.payload = JSON.stringify({data:values});

fetch(url+'/absjson',options,function(response_text){
    try{
        
        Browser.msgBox(JSON.parse(response_text).warn);
    }catch(ex){
        Browser.msgBox('[ERROR-0]'+response_text+ex);
    }

})


