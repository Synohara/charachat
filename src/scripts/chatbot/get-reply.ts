import { v4 as uuidv4 } from "uuid";
import ChatRequest from "../wiki-llm/ChatRequest";

export default async function getReply(
  message: string,
  convoState: any,
  command: string
) {
  // response loading
  convoState.setValue((cs: any) => ({ ...cs, turn: command }));

  let output = []
  try {
    output = await getAiOutput(convoState, message);
  } catch (error) {
    console.log(error);
    convoState.setValue((cs: any) => ({
      ...cs,
      turn: "user-answer",
    }));
    return [
      {
        id: uuidv4(),
        fromChatbot: true,
        text: "Oops! Something went wrong. Please refresh the page and try again.",
      },
    ];
  }

  const newInfo = {
    responses: [output[0]["agent_utterance"], output[1]["agent_utterance"]],
    logObjects: [output[0]["log_object"], output[1]["log_object"]],
  }

  convoState.setValue((cs: any) => ({
    ...cs,
    turn: "user-eval1",
    responseInfo: {
      ...cs.responseInfo,
      ...newInfo
    }
  }));

  return {
    ...convoState.value.responseInfo,
    ...newInfo
  }
}

async function getAiOutput(convoState, message) {
  let completionParameters = {}

  completionParameters["systems"] = convoState.value.responseInfo.systems;

  convoState.setValue((cs: any) => ({
    ...cs,
    responseInfo: {
      ...cs.responseInfo,
      dialogId: cs.responseInfo.dialogId ? cs.responseInfo.dialogId : uuidv4(),
    },
  }));

  const ri = convoState.value.responseInfo;

  let replies = [];
  if (convoState.value.autoPickMode) {
    // only need one request
    // first, push a dummy object for the first response
    replies.push({ agent_utterance: "", log_object: {} });
    // then, push the actual response for second response
    let reply = await ChatRequest(ri.experimentId, ri.dialogId, ri.turnId, message, ri.systems[1]);
    replies.push(reply);
  } else {
    for (let i = 0; i < 2; i++) {
      let reply = await ChatRequest(ri.experimentId, ri.dialogId, ri.turnId, message, ri.systems[i]);
      replies.push(reply);
    }
  }

  convoState.setValue((cs: any) => ({
    ...cs,
    responseInfo: {
      ...cs.responseInfo,
      turnId: cs.responseInfo.turnId + 1,
      rating: null,
    },
  }));

  return replies
}