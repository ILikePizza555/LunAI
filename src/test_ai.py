import ai

def test_context_window_sanity():
    window = ai.ContextWindow(10)
    assert window.empty == True

def test_context_window_insert_new_message_default_params():
    window = ai.ContextWindow(10)
    window.insert_new_message(ai.MessageRole.USER, "apple")

    actual = next(window.messages)
    assert actual == ai.Message(0, 0, ai.MessageRole.USER, "apple")

def test_context_window_queue_no_priority():
    window = ai.ContextWindow(10)
    window.insert_new_message(ai.MessageRole.USER, "apple")
    window.insert_new_message(ai.MessageRole.USER, "bing bing")
    window.insert_new_message(ai.MessageRole.USER, "bong bong")
    
    assert window.chat_order == [
        ai.Message(0, 0, ai.MessageRole.USER, "apple"),
        ai.Message(0, 1, ai.MessageRole.USER, "bing bing"),
        ai.Message(0, 2, ai.MessageRole.USER, "bong bong")
    ]

def test_context_window_queue_popped_no_priority():
    window = ai.ContextWindow(10)
    window.insert_new_message(ai.MessageRole.USER, "apple")
    window.insert_new_message(ai.MessageRole.USER, "bing bing")
    window.insert_new_message(ai.MessageRole.USER, "bong bong")
    window.insert_new_message(ai.MessageRole.USER, "banana_john")

    assert window.token_count == 10
    assert window.chat_order == [
        ai.Message(0, 1, ai.MessageRole.USER, "bing bing"),
        ai.Message(0, 2, ai.MessageRole.USER, "bong bong"),
        ai.Message(0, 3, ai.MessageRole.USER, "banana_john")
    ]
    
    window.insert_new_message(ai.MessageRole.USER, "foxtail software")

    assert window.token_count == 7
    assert window.chat_order == [
        ai.Message(0, 3, ai.MessageRole.USER, "banana_john"),
        ai.Message(0, 4, ai.MessageRole.USER, "foxtail software")
    ]

def test_context_window_queue_with_priority():
    window = ai.ContextWindow(20)
    window.insert_new_message(ai.MessageRole.SYSTEM, "You are a helpful assistant.", 1)
    window.insert_new_message(ai.MessageRole.USER, "Hello, can you tell me your name?")
    window.insert_new_message(ai.MessageRole.ASSISTANT, "John")

    assert window.token_count == 16
    assert window.chat_order == [
        ai.Message(1, 0, ai.MessageRole.SYSTEM, "You are a helpful assistant."),
        ai.Message(0, 1, ai.MessageRole.USER, "Hello, can you tell me your name?"),
        ai.Message(0, 2, ai.MessageRole.ASSISTANT, "John")
    ]

def test_context_window_queue_pop_with_priority():
    window = ai.ContextWindow(20)
    window.insert_new_message(ai.MessageRole.SYSTEM, "You are a helpful assistant.", 1) #6
    window.insert_new_message(ai.MessageRole.USER, "Hello, can you tell me your name?") #9
    window.insert_new_message(ai.MessageRole.ASSISTANT, "John") #1
    window.insert_new_message(ai.MessageRole.USER, "banana") #2
    window.insert_new_message(ai.MessageRole.ASSISTANT, "ackackackack")

    assert window.chat_order == [
        ai.Message(1, 0, ai.MessageRole.SYSTEM, "You are a helpful assistant."),
        ai.Message(0, 2, ai.MessageRole.ASSISTANT, "John"),
        ai.Message(0, 3, ai.MessageRole.USER, "banana"),
        ai.Message(0, 4, ai.MessageRole.ASSISTANT, "ackackackack")
    ]