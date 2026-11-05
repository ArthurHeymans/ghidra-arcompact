// SPDX-License-Identifier: Apache-2.0
// Only synthetic fixture functions; no arbitrary firmware C execution.
import com.google.gson.GsonBuilder;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Map;
import java.util.regex.Pattern;

public class CheckArcompactProbes extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path output = Path.of(getScriptArgs()[0]);
        Files.createDirectories(output);
        if (!currentProgram.getLanguageID().toString().equals("ARCompact:LE:32:default")) {
            throw new IllegalStateException("wrong language");
        }
        DecompInterface decompiler = new DecompInterface();
        if (!decompiler.openProgram(currentProgram)) throw new IllegalStateException("open failed");
        ArrayList<String> passed = new ArrayList<>();
        try {
            for (String name : new String[] {"probe_status_z", "probe_status_n", "probe_status_c",
                    "probe_status_v", "probe_lp_signed", "probe_lp_false_preserves_aux"}) {
                var matches = getGlobalFunctions(name);
                if (matches.size() != 1) throw new IllegalStateException("missing/ambiguous " + name);
                Function function = matches.get(0);
                var result = decompiler.decompileFunction(function, 15, monitor);
                if (!result.decompileCompleted() || result.getDecompiledFunction() == null) {
                    throw new IllegalStateException(name + ": " + result.getErrorMessage());
                }
                String code = result.getDecompiledFunction().getC();
                Files.writeString(output.resolve(name + ".c"), code);
                if (name.startsWith("probe_status_")) {
                    if (!Pattern.compile("\\breturn\\s+(?:1|0x1)\\s*;").matcher(code).find()) {
                        throw new IllegalStateException("lost live flags: " + code);
                    }
                } else if (code.contains("UNRECOVERED_JUMPTABLE") || code.contains("(*")) {
                    throw new IllegalStateException("lost loop flow: " + code);
                }
                passed.add(name);
            }
        } finally {
            decompiler.dispose();
        }
        Files.writeString(output.resolve("decompilation.json"), new GsonBuilder().setPrettyPrinting()
                .create().toJson(Map.of("passed", passed, "language", currentProgram.getLanguageID().toString())));
        println("ARCOMPACT_PROBES_COMPLETE");
    }
}
