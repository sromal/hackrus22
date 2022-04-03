import twilio_utils


def twilio_test():
    configs = twilio_utils.load_twilio_config()
    assert configs


def run_all_tests():
    twilio_test()


if __name__ == "__main__":
    run_all_tests()