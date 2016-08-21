import main as pycraft


def main():
    _, settings, _, _, _, _ = pycraft.setup()

    pycraft.setup_render_c(settings)

    save = pycraft.saves.new_save({'name': 'test', 'seed': 'This is a test!'})

    try:
        pycraft.game(pycraft.server_interface.LocalInterface('tester', save, 0), settings)
    finally:
        pycraft.setdown()


if __name__ == '__main__':
    main()
