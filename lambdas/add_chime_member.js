const AWS = require('aws-sdk');
const appInstanceUserArnHeader = 'x-amz-chime-bearer';


exports.handler = async (event) => {
  const { appInstanceArn, channelArn, mainUserId, userIdToAdd } = event;
  
  const chime = new AWS.Chime({
    region: 'us-east-1',
  });
  
  console.log("ADDING MEMBER");
  
  var params_mem = {
        ChannelArn: `${channelArn}`,
        MemberArn: `${appInstanceArn}/user/${userIdToAdd}`,
        Type: "DEFAULT"
    };

    let request_mem = chime.createChannelMembership(params_mem);
    request_mem.on('build', function() {
        request_mem.httpRequest.headers[appInstanceUserArnHeader] = `${appInstanceArn}/user/${mainUserId}`;
    });
    let response_mem = await request_mem.promise();
    
    return response_mem;
  
};
