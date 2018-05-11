import main as pycraft


def main():
    _, settings, _, _, benchmarks, _, _ = pycraft.setup()
    pycraft.render_interface.setup_render_module(settings)

    save = pycraft.saves.new_save({'name': 'test', 'seed': 'This is a test!'})
    server_obj = pycraft.server_interface.LocalInterface('tester', save, 0, settings)

    try:
        pycraft.game(server_obj, settings, benchmarks)
    finally:
        pycraft.setdown()


if __name__ == '__main__':
    main()
