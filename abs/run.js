
//

values.forEach(function(row,rn,rows){
    row.forEach(function(v,cn,cells){
        if(v instanceof Date) cells[cn] = 
            v.getYear()+'-'+(v.getMonth()+1)+'-'+v.getDate()
    })
})

var options = {};
options.method = "post";
options.headers = {'Content-Type':'application/json'};
options.payload = JSON.stringify({data:values});

fetch(url+'/absjson',options,function(response_text){
    try{
        resp = JSON.parse(response_text)
        if(resp.warn) Browser.msgBox(resp.warn);
        resp.out_seq.forEach(function(task,n,tasks){
            if(task.op==='set')
                rows.getCell(task.rn+1,task.cn+1).setValue(task.val);
        });
        
        //Browser.msgBox(response_text);
        
        
        
    }catch(ex){
        Browser.msgBox('[ERROR-0]'+response_text+ex);
    }

})


