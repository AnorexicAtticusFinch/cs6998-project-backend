const AWS = require('aws-sdk');
const appInstanceUserArnHeader = 'x-amz-chime-bearer';


exports.handler = async (event) => {
  const { appInstanceArn, name, sid, aid } = event;
  
  console.log(event);
  
  try {
  const chime = new AWS.Chime({
    region: 'us-east-1',
  });
  
  const params = {
    AppInstanceArn: appInstanceArn,
    Name: name,
    Mode: 'RESTRICTED',
    Privacy: 'PRIVATE'
  };
  
  const request = chime.createChannel(params);
  
  request.on('build', function() {
    request.httpRequest.headers[appInstanceUserArnHeader] = `${appInstanceArn}/user/${aid}`;
  });
  
  var response = "";

    response = await request.promise();
    // return response.ChannelArn;
    
    
    var params_mem = {
        ChannelArn: response.ChannelArn,
        MemberArn: `${appInstanceArn}/user/${sid}`,
        Type: "DEFAULT"
    };

    let request_mem = chime.createChannelMembership(params_mem);
    request_mem.on('build', function() {
        request_mem.httpRequest.headers[appInstanceUserArnHeader] = `${appInstanceArn}/user/${aid}`;
    });
    let response_mem = await request_mem.promise();
    
    console.log(response_mem);
    
    return {"status": "okay"}
    
    
  } catch (error) {
    console.log(error);
    return {"status": "error"}
  }

};
