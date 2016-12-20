import main as pycraft


def main():
    _, settings, _, _, _, _ = pycraft.setup()

    render_c = pycraft.import_render_c(settings)
    save = pycraft.saves.new_save({'name': 'test', 'seed': 'This is a test!'})
    server_obj = pycraft.server_interface.LocalInterface('tester', save, 0)

    try:
        pycraft.game(server_obj, settings, render_c)
    finally:
        pycraft.setdown()


if __name__ == '__main__':
    main()
