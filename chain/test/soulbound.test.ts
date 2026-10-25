import { createUmi } from "@metaplex-foundation/umi-bundle-defaults";
import { generateSigner, keypairIdentity, publicKey } from "@metaplex-foundation/umi";
import {
  create,
  getCreateV2InstructionDataSerializer,
  mplCore,
  MPL_CORE_PROGRAM_ID,
} from "@metaplex-foundation/mpl-core";
import { describe, expect, it } from "vitest";
import { buildCreateInput } from "../src/mint.js";

describe("soulbound create", () => {
  it("builds one permanent freeze plugin with authority None", () => {
    const umi = createUmi("http://127.0.0.1:8899").use(mplCore());
    const asset = generateSigner(umi);
    const input = buildCreateInput({
      asset,
      owner: publicKey(generateSigner(umi).publicKey),
      uri: "http://localhost:8100/api/chain/meta/asset.json",
    });
    expect(input.name).toBe("Cat Qubit Architect");
    expect(input.uri).toContain("/api/chain/meta/");
    expect(input.plugins).toEqual([
      { type: "PermanentFreezeDelegate", frozen: true, authority: { type: "None" } },
    ]);
  });

  it("encodes that plugin in the real Core create instruction", () => {
    const umi = createUmi("http://127.0.0.1:8899").use(mplCore());
    umi.use(keypairIdentity(umi.eddsa.generateKeypair()));
    const asset = generateSigner(umi);
    const input = buildCreateInput({
      asset,
      owner: String(generateSigner(umi).publicKey),
      uri: `http://localhost:8100/api/chain/meta/${asset.publicKey}.json`,
    });
    const instructions = create(umi, input).getInstructions();
    expect(instructions[0]?.programId).toBe(MPL_CORE_PROGRAM_ID);
    const [decoded] = getCreateV2InstructionDataSerializer().deserialize(instructions[0]!.data);
    const plugins = decoded.plugins;
    expect(plugins.__option).toBe("Some");
    if (plugins.__option !== "Some") return;
    const pair = plugins.value[0];
    expect(pair?.plugin.__kind).toBe("PermanentFreezeDelegate");
    if (pair?.plugin.__kind !== "PermanentFreezeDelegate") return;
    expect(pair.plugin.fields[0]?.frozen).toBe(true);
    expect(pair.authority.__option).toBe("Some");
    if (pair.authority.__option !== "Some") return;
    expect(pair.authority.value.__kind).toBe("None");
  });
});
