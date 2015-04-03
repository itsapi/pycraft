import terrain, saves


chunk_size = terrain.world_gen['chunk_size']


def load_chunks(save, meta, slice_list, blocks):
    new_slices = {}
    gen_slices = {}

    # Generates new terrain
    for chunk_num in set(i // chunk_size for i in slice_list):
        chunk = saves.load_chunk(save, chunk_num)
        for i in range(chunk_size):
            pos = i + chunk_num * chunk_size
            if not str(pos) in chunk:
                slice_ = terrain.gen_slice(pos, meta, blocks)
                chunk[str(pos)] = slice_
                gen_slices[str(pos)] = slice_
        new_slices.update(chunk)

    # Save generated terrain to file
    if gen_slices:
        saves.save_map(save, gen_slices)

    return new_slices
