// n8n Workflow Fix for Tool Display
// Update the "Format Success Response" node in n8n

// Replace the getPurpose function with this complete version:
function getPurpose(toolName) {
  const purposes = {
    'vector_search': 'Semantic search in knowledge base',
    'graph_search': 'Graph traversal for relationships',
    'get_entity_relationships': 'Entity relationship exploration',
    'entity_search': 'Find specific entities',
    'hybrid_search': 'Combined vector and graph search',
    'get_document': 'Retrieve full document',
    'list_documents': 'List available documents',
    'get_entity_timeline': 'Get temporal entity data'
  };
  return purposes[toolName] || 'General search';
}

// Full updated Format Success Response code:
const formatSuccessResponse = () => {
  // Helper function to describe tool purpose
  function getPurpose(toolName) {
    const purposes = {
      'vector_search': 'Semantic search in knowledge base',
      'graph_search': 'Graph traversal for relationships', 
      'get_entity_relationships': 'Entity relationship exploration',
      'entity_search': 'Find specific entities',
      'hybrid_search': 'Combined vector and graph search',
      'get_document': 'Retrieve full document',
      'list_documents': 'List available documents',
      'get_entity_timeline': 'Get temporal entity data'
    };
    return purposes[toolName] || 'General search';
  }

  // Extract and format the response
  const responseData = $input.first().json;
  
  // Get the assistant's response
  const assistantResponse = responseData.response || responseData.content || 'No response provided';
  
  // Extract tool usage information
  let toolsUsed = [];
  
  // Check for tool calls in the response
  if (responseData.tool_calls && Array.isArray(responseData.tool_calls)) {
    toolsUsed = responseData.tool_calls.map(call => ({
      name: call.tool_name || call.name,
      purpose: getPurpose(call.tool_name || call.name),
      arguments: call.arguments || {}
    }));
  } else if (responseData.tools_used && Array.isArray(responseData.tools_used)) {
    toolsUsed = responseData.tools_used.map(tool => ({
      name: typeof tool === 'string' ? tool : tool.name,
      purpose: getPurpose(typeof tool === 'string' ? tool : tool.name),
      arguments: typeof tool === 'object' ? tool.arguments : {}
    }));
  }
  
  // Format the final response
  const formattedResponse = {
    query: responseData.query || responseData.message || 'No query provided',
    response: assistantResponse,
    toolsUsed: toolsUsed,
    timestamp: new Date().toISOString(),
    processingTime: responseData.processing_time || 'Not measured',
    confidence: responseData.confidence || null
  };
  
  return {
    json: formattedResponse
  };
};

// Execute the function
return formatSuccessResponse();