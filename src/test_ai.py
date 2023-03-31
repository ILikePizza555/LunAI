import ai

def test_context_window_sanity():
    window = ai.ContextWindow(10)
    assert window.empty == True

def test_context_window_insert_new_message_default_params():
    window = ai.ContextWindow(10)
    window.insert_new_message(ai.MessageRole.USER, "apple")

    actual = window.message_iterator[0]
    assert actual == ai.Message(0, 0, ai.MessageRole.USER, "apple")

def test_context_window_queue_no_priority():
    window = ai.ContextWindow(10)
    window.insert_new_message(ai.MessageRole.USER, "apple")
    window.insert_new_message(ai.MessageRole.USER, "bing bing")
    window.insert_new_message(ai.MessageRole.USER, "bong bong")
    
    actual = list(window.message_iterator)
    assert actual == [
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

    actual = list(window.message_iterator)
    assert window.token_count == 10
    assert actual == [
        ai.Message(0, 1, ai.MessageRole.USER, "bing bing"),
        ai.Message(0, 2, ai.MessageRole.USER, "bong bong"),
        ai.Message(0, 3, ai.MessageRole.USER, "banana_john")
    ]
    
    window.insert_new_message(ai.MessageRole.USER, "foxtail software")

    actual = list(window.message_iterator)
    assert window.token_count == 7
    assert actual == [
        ai.Message(0, 3, ai.MessageRole.USER, "banana_john"),
        ai.Message(0, 4, ai.MessageRole.USER, "foxtail software")
    ]