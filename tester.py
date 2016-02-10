import main as pycraft


def main():
    save = pycraft.saves.new_save({'name': 'test', 'seed': 'This is a test!'})
    blocks = pycraft.render.gen_blocks()
    pycraft.game(blocks, {}, *pycraft.saves.load_save(save))


if __name__ == '__main__':
    main()
