import pygame
import random
import time
import queue
from mods.blink_detect import BlinkDetectionThread  # Assuming the class above is saved in BlinkDetectionThread.py
from mods.audio_detect import SpeechRecognitionThread  # Replace with your actual module name

def run_game(surface, level_width, level_height, win_width, win_height, max_attempts_arg):
    # Blink detection setup
    blink_queue = queue.Queue()
    blink_thread = BlinkDetectionThread(blink_queue)
    blink_thread.start()  # Start the blink detection thread

    # speech detection setup
    speech_queue = queue.Queue(maxsize=10)
    speech_thread = SpeechRecognitionThread(audio_queue=speech_queue, language="english")
    speech_thread.start()

    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    LIGHT_GRAY = (200, 200, 200)
    DARK_GRAY = (100, 100, 100)

    # Fonts
    FONT = pygame.font.Font(None, 36)

    # Cause-Effect pairs
    cause_effect_pairs = [
        ("Dark clouds gathered in the sky.", "It started raining."),
        ("They received plenty of sunlight and water.", "The plants grew tall."),
        ("The battery was dead.", "The car wouldn't start."),
        ("Someone turned off the light.", "The room became dark."),
        ("It was set to go off at 7 AM.", "The alarm clock rang."),
        ("The temperature increased.", "The ice melted."),
        ("It was left in the oven too long.", "The cake burned."),
        ("There was a lot of smoke in the air.", "People were coughing."),
        ("There was a power outage.", "The computer shut down unexpectedly."),
        ("It was dropped on the ground.", "The phone's screen cracked."),
    ]
    random.shuffle(cause_effect_pairs)

    # Helper function to generate options
    def generate_options(correct_cause, all_causes, num_options=4):
        options = [correct_cause]
        distractors = [cause for cause in all_causes if cause != correct_cause]
        random.shuffle(distractors)
        options.extend(distractors[:num_options - 1])
        random.shuffle(options)
        return options

    clock = pygame.time.Clock()
    running = True
    current_index = 0
    selected_option = 0  # Track the current highlighted option
    options = []
    option_rects = []
    options_generated = False
    show_feedback = False
    feedback = ""
    feedback_time = 0
    attempts = 0
    max_attempts = max_attempts_arg
    weights = [2, 3, 5]  # Increasing weights for each attempt
    results = [0, 0, 0]

    # Prepare all causes for option generation
    all_causes = [pair[0] for pair in cause_effect_pairs]

    start_time = time.time()

    while running and attempts < max_attempts:
        start_time = time.time()  # Start timing the attempt

        # Handle Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                blink_thread.stop()  # Stop the blink detection thread
                return
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(options)
                elif event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if current_index < len(cause_effect_pairs):
                        correct_cause, effect = cause_effect_pairs[current_index]
                        if options[selected_option] == correct_cause:
                            results[attempts] = weights[attempts]
                            feedback = "Correct!"
                        else:
                            feedback = f"Incorrect! The correct cause was: {correct_cause}"
                        show_feedback = True
                        feedback_time = pygame.time.get_ticks()
                        attempts += 1

        # Handle blink input
        try:
            blink_message = blink_queue.get_nowait()
            if blink_message == "SINGLE_BLINK":
                # Toggle options using single blink
                selected_option = (selected_option + 1) % len(options)
            elif blink_message == "DOUBLE_BLINK":
                # Submit selected option using double blink
                if current_index < len(cause_effect_pairs):
                    correct_cause, effect = cause_effect_pairs[current_index]

                    if options[selected_option] == correct_cause:
                        results[attempts] = weights[attempts]
                        feedback = "Correct!"
                    else:
                        feedback = f"Incorrect! The correct cause was: {correct_cause}"
                       
                    show_feedback = True
                    feedback_time = pygame.time.get_ticks()
                    attempts += 1  # Increment attempts
        except queue.Empty:
            pass


        # Speech Control
        try:
            if not speech_queue.empty():
                command = speech_queue.get(block=False)
                print(f"Recognized command: {command}")
                if command == "down":
                    selected_option = (selected_option + 1) % len(options)
                elif command == "up":
                    selected_option = (selected_option - 1) % len(options)
                elif command == "select":
                    # Submit selected option using double blink
                    if current_index < len(cause_effect_pairs):
                        correct_cause, effect = cause_effect_pairs[current_index]

                        if options[selected_option] == correct_cause:
                            results[attempts] = weights[attempts]
                            feedback = "Correct!"
                        else:
                            feedback = f"Incorrect! The correct cause was: {correct_cause}"
                            
                        show_feedback = True
                        feedback_time = pygame.time.get_ticks()
                        attempts += 1  # Increment attempts
        except queue.Empty:
            pass


        # Clear the surface
        surface.fill(WHITE)

        if current_index < len(cause_effect_pairs):
            # Display the current effect
            correct_cause, effect = cause_effect_pairs[current_index]
            effect_surface = FONT.render("Effect: " + effect, True, BLACK)
            surface.blit(effect_surface, (50, 50))

            # Generate options only once per question
            if not options_generated:
                options = generate_options(correct_cause, all_causes)
                option_rects = []
                for idx, option in enumerate(options):
                    rect = pygame.Rect(50, 150 + idx * 60, level_width - 100, 50)
                    option_rects.append(rect)
                options_generated = True  # Set the flag to True after generating options

            # Display the options
            for idx, option in enumerate(options):
                rect = option_rects[idx]
                color = DARK_GRAY if idx == selected_option else LIGHT_GRAY  # Highlight selected option
                pygame.draw.rect(surface, color, rect)
                option_surface = FONT.render(option, True, BLACK)
                surface.blit(option_surface, (rect.x + 10, rect.y + 10))

            # Display feedback for 2 seconds
            if show_feedback:
                feedback_surface = FONT.render(feedback, True, BLACK)
                surface.blit(feedback_surface, (50, level_height - 100))
                if pygame.time.get_ticks() - feedback_time > 2000:
                    show_feedback = False
                    current_index += 1
                    options_generated = False  # Reset the flag for the next question
                    selected_option = 0  # Reset selection to the first option
                    if current_index >= len(cause_effect_pairs):
                        running = False
        else:
            # End the game
            running = False

        pygame.display.update()
        clock.tick(30)

    end_time = time.time()-start_time

    blink_thread.stop()  # Stop the blink detection thread
    print("results", results, end_time)
    return results, end_time
