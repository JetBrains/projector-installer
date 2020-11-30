// Inspired from https://github.com/actions/upload-release-asset/issues/47#issuecomment-698722668

// upload all files from '/dist' dir to release assets
module.exports = async ({github, context, releaseId}) => {
    const fs = require('fs');
    const artifactDir = './dist/';
    for (const fileName of fs.readdirSync(artifactDir)) {
        const artifactPath = artifactDir + fileName
        console.log('uploadReleaseAsset', artifactPath);
        await github.repos.uploadReleaseAsset({
            owner: context.repo.owner,
            repo: context.repo.repo,
            release_id: releaseId,
            name: fileName,
            data: await fs.readFileSync(artifactPath),
        });
    }
}
